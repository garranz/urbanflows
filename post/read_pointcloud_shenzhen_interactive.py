#!/usr/bin/env python3
"""
Interactive probe visualization tool.
Click on probe points to display velocity profiles at that location.
"""

from CTGlibD.ngpost import *
from extractcity import stl_to_2d_view
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, CheckButtons
import numpy as np
from pathlib import Path

datapath = Path('../data')


class ProbeVisualizer:
    def __init__(self):
        self.Nx, self.Ny, self.Nz = 9, 10, 30
        self.basenms = (
            'shenzhen_x2200_y1600_dummy_2',
            #'shenzhen_x1600_y800_dummy_2',
            'shenzhen_x1600_y800_dummy_3',
            'shenzhen_r1200_dummy_2',
        )
        self.case_labels = ('x2200_y1600_2', 'x1600_y800_3', 'r1200_2')
        self.colors = ('tab:blue', 'tab:orange', 'tab:green')
        
        # Data storage: {case_idx: {(i,j): {'vel_avg': ..., 'vel_rms': ..., ...}}}
        self.data = {}
        self.grid_coords = {}  # {case_idx: {'x_vals', 'y_vals', 'z_vals'}}
        self.point_map = {}    # Maps (x, y) -> (case_idx, i, j)
        
        self.selected_point = None
        self.load_data()
        self.setup_gui()
        
    def load_data(self):
        """Load all probe data from both cases."""
        for kb_, basenm in enumerate(self.basenms):
            pp = PointCloud(datapath / basenm / 'pcprobes', 'points')
            x, y, z = pp.getpoints()
            
            x_vals = np.unique(x)
            y_vals = np.unique(y)
            z_vals = np.unique(z)
            
            Nx, Ny, Nz = len(x_vals), len(y_vals), len(z_vals)
            print(f"Case {kb_}: Nx={Nx}, Ny={Ny}, Nz={Nz}")
            
            x_idx = {val: i for i, val in enumerate(x_vals)}
            y_idx = {val: i for i, val in enumerate(y_vals)}
            z_idx = {val: i for i, val in enumerate(z_vals)}
            
            self.grid_coords[kb_] = {
                'x_vals': x_vals,
                'y_vals': y_vals,
                'z_vals': z_vals,
                'Nx': Nx, 'Ny': Ny, 'Nz': Nz
            }
            
            vel_avg = np.full((3, Nx, Ny, Nz), np.nan)
            vel_rms = np.full((3, Nx, Ny, Nz), np.nan)
            vel_rey = np.full((3, Nx, Ny, Nz), np.nan)
            
            dat = pp.getdata(pp.getifrl()[-1])
            
            for xv, yv, zv, dd in zip(x, y, z, dat.T):
                i, j, k = x_idx[xv], y_idx[yv], z_idx[zv]
                for r_ in range(3):
                    vel_avg[r_, i, j, k] = dd[pp.vlist.index(f'AVG(U)[{r_}]')]
                    vel_rms[r_, i, j, k] = dd[pp.vlist.index(f'RMS(U)[{r_}]')]
                    vel_rey[r_, i, j, k] = dd[pp.vlist.index(f'REY(U)[{r_}]')]
            
            self.data[kb_] = {
                'vel_avg': vel_avg,
                'vel_rms': vel_rms,
                'vel_rey': vel_rey
            }
            
            # Build point map for this case
            for i, xv in enumerate(x_vals):
                for j, yv in enumerate(y_vals):
                    key = (xv, yv)
                    if key not in self.point_map:
                        self.point_map[key] = []
                    self.point_map[key].append((kb_, i, j))
    
    def setup_gui(self):
        """Set up the interactive GUI."""
        # Main figure: city map with probe points
        self.fig_map, self.ax_map = plt.subplots(figsize=(10, 8))
        self.fig_map.canvas.manager.set_window_title('Probe Locations (click to select)')
        
        # Plot city buildings
        builds = stl_to_2d_view('../stl/shenzhen_buildings.stl')
        self.ax_map.add_collection(builds)
        self.ax_map.autoscale()
        
        # Plot probe points (use first case for positions)
        gc = self.grid_coords[0]
        x_vals, y_vals = gc['x_vals'], gc['y_vals']
        
        # Create scatter plot with picker enabled
        xx, yy = np.meshgrid(x_vals, y_vals, indexing='ij')
        self.scatter = self.ax_map.scatter(
            xx.flatten(), yy.flatten(),
            s=80, c='tab:blue', edgecolors='k', linewidths=0.5,
            picker=True, pickradius=10, zorder=10
        )
        
        # Store flattened coordinates for picker
        self.scatter_x = xx.flatten()
        self.scatter_y = yy.flatten()
        
        # Highlight marker for selected point
        self.highlight, = self.ax_map.plot([], [], 'o', ms=20, mfc='none',
                                            mec='red', mew=3, zorder=11)
        
        self.ax_map.set_xlabel(r'$x$ [m]')
        self.ax_map.set_ylabel(r'$y$ [m]')
        self.ax_map.set_title('Click on a probe point to view profiles')
        
        # Profile figure: 3x3 grid for profiles
        self.fig_prof, self.axes_prof = plt.subplots(3, 3, figsize=(12, 10), sharey=True)
        self.fig_prof.canvas.manager.set_window_title('Velocity Profiles')
        
        # Labels for plots
        self.avg_labels = [r'$\langle U \rangle$', r'$\langle V \rangle$', r'$\langle W \rangle$']
        self.rms_labels = [r'$u_{rms}$', r'$v_{rms}$', r'$w_{rms}$']
        self.rey_labels = [r"$\langle u'v' \rangle$", r"$\langle u'w' \rangle$", r"$\langle v'w' \rangle$"]
        
        # Initialize empty profile lines (one per case)
        self.profile_lines = {}
        for kb_ in range(len(self.basenms)):
            self.profile_lines[kb_] = {
                'avg': [], 'rms': [], 'rey': []
            }
            for row in range(3):
                for col, cat in enumerate(['avg', 'rms', 'rey']):
                    line, = self.axes_prof[row, col].plot(
                        [], [], '-o', ms=3, lw=1,
                        color=self.colors[kb_], label=self.case_labels[kb_]
                    )
                    self.profile_lines[kb_][cat].append(line)
        
        # Set up axes labels
        for col, labels in enumerate([self.avg_labels, self.rms_labels, self.rey_labels]):
            for row in range(3):
                self.axes_prof[row, col].set_xlabel(labels[row])
                self.axes_prof[row, col].grid(True, alpha=0.3)
                if col == 0:
                    self.axes_prof[row, col].set_ylabel(r'$z$ [m]')
        
        # Add legend
        self.axes_prof[0, 0].legend(loc='upper right', fontsize=8)
        
        self.fig_prof.suptitle('Select a probe point on the map')
        self.fig_prof.tight_layout()
        
        # Connect click event
        self.fig_map.canvas.mpl_connect('pick_event', self.on_pick)
        
    def on_pick(self, event):
        """Handle click on probe point."""
        if event.artist != self.scatter:
            return
            
        ind = event.ind[0]  # Get first picked point
        x_click = self.scatter_x[ind]
        y_click = self.scatter_y[ind]
        
        self.update_selection(x_click, y_click)
        
    def update_selection(self, x_sel, y_sel):
        """Update the selected point and refresh profiles."""
        self.selected_point = (x_sel, y_sel)
        
        # Update highlight marker
        self.highlight.set_data([x_sel], [y_sel])
        self.fig_map.canvas.draw_idle()
        
        # Get point indices for all cases
        key = (x_sel, y_sel)
        if key not in self.point_map:
            print(f"No data for point ({x_sel}, {y_sel})")
            return
            
        # Update profiles for each case
        for kb_, i, j in self.point_map[key]:
            gc = self.grid_coords[kb_]
            z_vals = gc['z_vals']
            
            vel_avg = self.data[kb_]['vel_avg']
            vel_rms = self.data[kb_]['vel_rms']
            vel_rey = self.data[kb_]['vel_rey']
            
            # Update average velocity profiles
            for comp in range(3):
                self.profile_lines[kb_]['avg'][comp].set_data(
                    vel_avg[comp, i, j, :], z_vals
                )
                
            # Update RMS profiles
            for comp in range(3):
                self.profile_lines[kb_]['rms'][comp].set_data(
                    vel_rms[comp, i, j, :], z_vals
                )
                
            # Update Reynolds stress profiles
            for comp in range(3):
                self.profile_lines[kb_]['rey'][comp].set_data(
                    vel_rey[comp, i, j, :], z_vals
                )
        
        # Rescale axes
        for row in range(3):
            for col in range(3):
                self.axes_prof[row, col].relim()
                self.axes_prof[row, col].autoscale_view()
        
        self.fig_prof.suptitle(f'Profiles at x={x_sel:.0f} m, y={y_sel:.0f} m')
        self.fig_prof.canvas.draw_idle()
        
    def run(self):
        """Start the interactive visualization."""
        plt.show()


if __name__ == "__main__":
    viz = ProbeVisualizer()
    viz.run()

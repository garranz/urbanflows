// figs/boundary_layer.typ
#import "@preview/cetz:0.5.0"
#import "colors.typ": myc1-light, myc2-light

#let domain_fig = cetz.canvas({
    import cetz.draw: *

    // --- Parameters ---
    let R = 4.0 // cylindrical domain radius
    let L = .5 // urban square half-side
    let n = 8 // number of BC sectors

    let bc = 1 // number of BC sectors

    // --- Domain background ---
    circle((0, 0), radius: R, fill: rgb("#f7f7f7"), stroke: none)
    rect((-L, -L), (L, L), fill: rgb("#e8e8e8"), stroke: none)

    line((0, 0), (0, R), stroke: (paint: gray, thickness: 0.7pt))

    // --- Buildings: grid with pseudo-random jitter and sizes ---
    let nx = 6
    let ny = 6
    let margin = .9
    let step = (2 * L - 2 * margin) / (nx - 1)
    for i in range(nx) {
      for j in range(ny) {
        let cx = -L + margin + i * step
        let cy = -L + margin + j * step
        let jx = calc.sin(i * 1.73 + j * 2.41) * L / 10
        let jy = calc.cos(i * 2.17 + j * 1.31) * L / 10
        let w = L / 10 + calc.abs(calc.sin(i * 3.1 + j * 0.7)) * L / 5
        let h = L / 10 + calc.abs(calc.cos(i * 0.9 + j * 2.8)) * L / 5
        rect(
          (cx + jx - w / 2, cy + jy - h / 2),
          (cx + jx + w / 2, cy + jy + h / 2),
          fill: rgb("#555555"),
          stroke: (paint: black, thickness: 0.4pt),
        )
      }
    }

    // --- Urban domain outline (on top of buildings) ---
    rect((-L, -L), (L, L), stroke: (paint: black, thickness: .5pt, dash: "dashed"), fill: none)


    // --- Boundary: 8 sectors with alternating colors ---
    let sc = (myc1-light, myc2-light)
    for i in range(n) {
      let a1 = i * 360 / n * 1deg
      let a2 = (i + 1) * 360 / n * 1deg
      arc((0, 0), start: a1, stop: a2, radius: R, anchor: "origin", stroke: (
        //paint: sc.at(calc.rem(i, 2)),
        paint: if calc.rem(i + bc, 8) < 4 { sc.at(0) } else { sc.at(1) },
        thickness: 2.5pt,
      ))
      // --- Radial tick marks between sectors ---
      line(
        (R * 0.96 * calc.cos(a1), R * 0.96 * calc.sin(a1)),
        (R * 1.04 * calc.cos(a1), R * 1.04 * calc.sin(a1)),
        stroke: (paint: black, thickness: 1pt),
      )
      // --- Sector labels ---
      let r = R + 0.35
      let a = (i + 4.5) * 360 / n * 1deg
      content(
        (r * calc.cos(a), r * calc.sin(a)),
        text(size: 9pt)[BC#sub[#(i)]],
      )
    }
    // --- Input/output
    let a = calc.rem(bc + 4, 8) * 360 / n * 1deg
    line((0, 0), (R * calc.cos(-a), R * calc.sin(-a)))
    arc((0, 0), stop: 90deg, start: 360deg - a, radius: R / 2, anchor: "origin",
    name: "a-arc", stroke: (paint: gray, thickness: 1pt))
    content("a-arc.arc-center", text(size: 10pt)[$alpha$], anchor: "south", padding: 0.15)

    // --- Annotations ---
    content((0, -L - 0.45), text(size: 10pt, style: "italic")[Urban domain])
    //content((R * 0.6, R * 0.6), text(size: 12pt, style: "italic")[$Omega$])

    // --- Axes ---
    //line((0, 0), (R + 1.1, 0), stroke: (paint: gray, thickness: 0.7pt), mark: (end: ">"))
    //line((0, 0), (0, R + 1.1), stroke: (paint: gray, thickness: 0.7pt), mark: (end: ">"))
    //content((R + 1.35, 0), text(size: 10pt)[$x$])
    //content((0, R + 1.35), text(size: 10pt)[$y$])

    line((L, 0), (R, 0), name: "cota", stroke: (paint: rgb("#222222"), thickness: 0.5pt), 
    mark: (start: ">", end: ">", fill: rgb("#222222"), scale: 0.8))

    content("cota.mid", text(size: 10pt)[$1200 "m"$], anchor: "south", padding: 0.15)


})

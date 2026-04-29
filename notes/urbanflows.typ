#import "@preview/cetz:0.5.0"

#import "./figs/domain.typ": domain_fig

#set math.equation(numbering: "(1)")
#set par(justify: true)

#set heading(numbering: "1.")
#show heading.where(level: 1): set block(below: 1em, above: 2.5em)
#show heading.where(level: 2): set block(above: 2em)

// smaller, justified, bold label
#show figure.caption: it => block(
  width: 95%, inset: (x: 0em),
)[
  #set text(size: 10pt)
  #set par(justify: true)
  *#it.supplement #context it.counter.display(): * #it.body
]
#show figure: set block(below: 2em, above: 1em)

#let maketitle(
  title: "",
  authors: (),
  date: datetime.today().display("[month repr:long] [day], [year]"),
  //date: none,
) = {
  set document(author: authors, title: title)
  // Author information.
  let authors-text = {
    set text(size: 1.1em)
    pad(top: 0.5em, bottom: 0.5em, x: 2em, grid(
      columns: (1fr,) * calc.min(3, authors.len()),
      gutter: 1em,
      ..authors.map(author => align(center, author)),
    ))
  }

  // Title row.
  align(center)[
    #v(60pt)
    #block(text(weight: 400, 18pt, title))//1.75em, title))
    #v(1em, weak: true)
    #authors-text
    #v(1em, weak: true)
    #block(text(weight: 400, 1.1em, date))
    #v(20pt)
  ]
}

#maketitle(
  title: "Wall-model Large-eddy simulations of urban flows",
  authors: (
    "Gonzalo Arranz",
  ),
)


= Methodology

== Computational domain

#figure(
  domain_fig,
  caption: [Top view of the computational setup. The urban domain is centered in
a cylindrical domain. The total radius is computed such that there is an offset
  of $1200 "m"$ between the urban area boundaries and the cylinder. The
  cylindrical boundary is split into 8 segments, denoted as $"BC"_i, i =
  0,...,8$. Four contigous segments are set as inflow (red) and the rest as
  outflow (blue). The boundaries are defined based on the wind direction
  $alpha$. ], gap: 2em,
)

For the inflow boundary condition we impose an atmospheric turbulent boundary
layer, $U_("ABL")(z)$ taking into account the wind direction:
$ 
U(z) = U_("ABL")(z) cos alpha quad quad
V(z) = U_("ABL")(z) sin alpha
$
= Results

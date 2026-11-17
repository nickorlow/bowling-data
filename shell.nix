{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (python-pkgs: [
      python-pkgs.pandas
      python-pkgs.requests
      python-pkgs.numpy
      python-pkgs.scipy
      python-pkgs.polars
      python-pkgs.jinja2
      python-pkgs.black
    ]))
  ];
}

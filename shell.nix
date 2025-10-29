{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.pygame
    python312Packages.python-lsp-ruff
  ];
}

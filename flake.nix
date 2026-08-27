{
  description = "Schematics and KiCad";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          system = system;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.kicad
            pkgs.ngspice
            pkgs.python3
            pkgs.jdk25
          ];

          shellHook = ''
            echo "~~~BINARY~~~"
            echo "launch via 'kicad PATH_TO_PROJECT' such as"
            echo "kicad ./standard_puzzle_module/standard_puzzle_box.kicad_pro"

            echo "~~~THEME~~~"
            echo "install kicad theme manually from 'kicad-gruvbox-theme'"
            echo "https://github.com/AlexanderBrevig/kicad-gruvbox-theme"
            # Locate and export the Python bindings provided by KiCad
            if [ -d "${pkgs.kicad}/lib/python3.11/site-packages" ]; then
              export PYTHONPATH="${pkgs.kicad}/lib/python3.11/site-packages:$PYTHONPATH"
            elif [ -d "${pkgs.kicad}/lib/python3.12/site-packages" ]; then
              export PYTHONPATH="${pkgs.kicad}/lib/python3.12/site-packages:$PYTHONPATH"
            fi
          '';
        };
      });
}

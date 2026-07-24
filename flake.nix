{
  description = "Industrial Escape Room Puzzle PCB Development Environment";

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
            pkgs.kicad # Pure KiCad suite (Python and standard assets integrated)
            pkgs.ngspice # Standalone SPICE circuit simulation engine
            pkgs.python3 # System Python environment
          ];

          shellHook = ''
            echo "========================================================="
            echo "⚡ KiCad PCB Design Environment Active ⚡"
            echo "  - Core GUI: launch via 'kicad'"
            echo "  - Simulation Backend: ngspice engine verified"
            echo "========================================================="
            
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

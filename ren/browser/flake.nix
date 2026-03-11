{
  description = "Ren Browser - A browser for the Reticulum Network";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        rns = pkgs.python3Packages.buildPythonPackage rec {
          pname = "rns";
          version = "1.0.4";
          format = "pyproject";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-5wZnp2f+Ujurjn6gYnRHJYxOZ2O3dW+7pQxlVtu4Q5k=";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            cryptography
            pyserial
            netifaces
          ];

          doCheck = false;
        };

        flet = pkgs.python3Packages.buildPythonPackage rec {
          pname = "flet";
          version = "0.28.3";
          format = "pyproject";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-0000000000000000000000000000000000000000000000000000000000000000";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            flet-core
            oauthlib
            httpx
            websockets
            watchdog
          ];

          doCheck = false;
        };

        ren-browser = pkgs.python3Packages.buildPythonPackage rec {
          pname = "ren-browser";
          version = "0.2.2";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs.python3Packages; [
            hatchling
            setuptools
            wheel
          ];

          propagatedBuildInputs = [
            flet
            rns
          ];

          doCheck = false;
        };

        pythonWithRenBrowser = pkgs.python3.withPackages (ps: with ps; [
          ren-browser
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ 
            pkgs.python3
            pkgs.poetry
            pkgs.mpv
          ];

          shellHook = ''
            TMP_LIB_DIR=$(mktemp -d)
            if [ -f "${pkgs.mpv}/lib/libmpv.so.2" ] && [ ! -f "$TMP_LIB_DIR/libmpv.so.1" ]; then
              ln -s "${pkgs.mpv}/lib/libmpv.so.2" "$TMP_LIB_DIR/libmpv.so.1" 2>/dev/null || true
            fi
            export LD_LIBRARY_PATH="$TMP_LIB_DIR:${pkgs.mpv}/lib:${pkgs.lib.makeLibraryPath [ pkgs.mpv ]}:$LD_LIBRARY_PATH"
            echo "Ren Browser development environment"
            echo "Python: $(python3 --version)"
            echo "Poetry is available for dependency management"
            echo "Run: poetry install --with dev"
          '';
        };

        packages.default = ren-browser;

        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "ren-browser" ''
            set -e
            cd ${self}
            export POETRY_VENV_IN_PROJECT=1
            TMP_LIB_DIR=$(mktemp -d)
            trap "rm -rf $TMP_LIB_DIR" EXIT
            if [ -f "${pkgs.mpv}/lib/libmpv.so.2" ] && [ ! -f "$TMP_LIB_DIR/libmpv.so.1" ]; then
              ln -s "${pkgs.mpv}/lib/libmpv.so.2" "$TMP_LIB_DIR/libmpv.so.1"
            fi
            export LD_LIBRARY_PATH="$TMP_LIB_DIR:${pkgs.mpv}/lib:${pkgs.lib.makeLibraryPath [ pkgs.mpv ]}:$LD_LIBRARY_PATH"
            if [ ! -d ".venv" ] || [ ! -f ".venv/bin/python" ]; then
              ${pkgs.poetry}/bin/poetry install --no-interaction 2>/dev/null || true
            fi
            exec ${pkgs.poetry}/bin/poetry run ren-browser "$@"
          ''}/bin/ren-browser";
        };

        apps.web = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "ren-browser-web" ''
            set -e
            cd ${self}
            export POETRY_VENV_IN_PROJECT=1
            TMP_LIB_DIR=$(mktemp -d)
            trap "rm -rf $TMP_LIB_DIR" EXIT
            if [ -f "${pkgs.mpv}/lib/libmpv.so.2" ] && [ ! -f "$TMP_LIB_DIR/libmpv.so.1" ]; then
              ln -s "${pkgs.mpv}/lib/libmpv.so.2" "$TMP_LIB_DIR/libmpv.so.1"
            fi
            export LD_LIBRARY_PATH="$TMP_LIB_DIR:${pkgs.mpv}/lib:${pkgs.lib.makeLibraryPath [ pkgs.mpv ]}:$LD_LIBRARY_PATH"
            if [ ! -d ".venv" ] || [ ! -f ".venv/bin/python" ]; then
              ${pkgs.poetry}/bin/poetry install --no-interaction 2>/dev/null || true
            fi
            exec ${pkgs.poetry}/bin/poetry run ren-browser-web "$@"
          ''}/bin/ren-browser-web";
        };

        apps.android = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "ren-browser-android" ''
            exec ${pythonWithRenBrowser}/bin/python -c "from ren_browser.app import android; android()" "$@"
          ''}/bin/ren-browser-android";
        };

        apps.ios = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "ren-browser-ios" ''
            exec ${pythonWithRenBrowser}/bin/python -c "from ren_browser.app import ios; ios()" "$@"
          ''}/bin/ren-browser-ios";
        };
      }
    );
}


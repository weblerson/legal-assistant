{
    pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
    name = "legal_assistant";
    buildInputs = [
        pkgs.uv
        pkgs.python312
        pkgs.redis
    ];
    shellHook = ''
        echo "Welcome to Legal Assistant project!!!"
    '';
}


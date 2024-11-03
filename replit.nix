{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.unzip
    pkgs.zip
    pkgs.cmake
    pkgs.git
    pkgs.openssl
    pkgs.postgresql
  ];
}

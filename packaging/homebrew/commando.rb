class Commando < Formula
  desc "A GNOME application for saving and running user-defined Linux commands"
  homepage "https://github.com/commando/commando"
  url "https://github.com/commando/commando/archive/v0.1.0.tar.gz"
  sha256 "SKIP"
  license "GPL-3.0-or-later"

  depends_on "python@3.11"
  depends_on "gtk+4"
  depends_on "libadwaita"
  depends_on "vte"
  depends_on "webkitgtk"

  def install
    system "python3", "-m", "pip", "install", "--prefix=#{prefix}", "."
  end

  test do
    system "#{bin}/commando", "--version"
  end
end


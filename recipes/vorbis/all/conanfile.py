from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version
import os

required_conan_version = ">=2.1"


class VorbisConan(ConanFile):
    name = "vorbis"
    description = "The VORBIS audio codec library"
    topics = ("audio", "codec")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://xiph.org/vorbis/"
    license = "BSD-3-Clause"
    package_type = "library"
    settings = "os", "arch", "build_type", "compiler"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("ogg/1.3.5", transitive_headers=True, transitive_libs=True)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Relocatable shared lib on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support
        if Version(self.version) > "1.3.7": # pylint: disable=conan-unreachable-upper-version
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Vorbis")
        # see https://github.com/conan-io/conan-center-index/pull/4173
        self.cpp_info.set_property("pkg_config_name", "vorbis-all-do-not-use")

        # vorbis
        self.cpp_info.components["vorbismain"].set_property("cmake_target_name", "Vorbis::vorbis")
        self.cpp_info.components["vorbismain"].set_property("pkg_config_name", "vorbis")
        self.cpp_info.components["vorbismain"].libs = ["vorbis"]
        if self.settings.os in ["Linux", "FreeBSD", "Android"]:
            self.cpp_info.components["vorbismain"].system_libs.append("m")
        if self.settings.os == "Android":
            self.cpp_info.components["vorbismain"].system_libs.append("log")
        self.cpp_info.components["vorbismain"].requires = ["ogg::ogg"]

        # TODO: Upstream VorbisConfig.cmake defines components 'Enc' and 'File',
        # which are related to imported targets Vorbis::vorbisenc and Vorbis::vorbisfile
        # Find a way to emulate this in CMakeDeps. See https://github.com/conan-io/conan/issues/10258

        # vorbisenc
        self.cpp_info.components["vorbisenc"].set_property("cmake_target_name", "Vorbis::vorbisenc")
        self.cpp_info.components["vorbisenc"].set_property("pkg_config_name", "vorbisenc")
        self.cpp_info.components["vorbisenc"].libs = ["vorbisenc"]
        self.cpp_info.components["vorbisenc"].requires = ["vorbismain"]

        # vorbisfile
        self.cpp_info.components["vorbisfile"].set_property("cmake_target_name", "Vorbis::vorbisfile")
        self.cpp_info.components["vorbisfile"].set_property("pkg_config_name", "vorbisfile")
        self.cpp_info.components["vorbisfile"].libs = ["vorbisfile"]
        self.cpp_info.components["vorbisfile"].requires = ["vorbismain"]

        # vorbisenc-alias
        self.cpp_info.components["vorbisenc-alias"].requires.append("vorbisenc")
        self.cpp_info.components["vorbisfile-alias"].requires.append("vorbisfile")

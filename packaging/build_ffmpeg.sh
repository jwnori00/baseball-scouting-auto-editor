#!/usr/bin/env bash
# Windows build from the official FFmpeg mirror and VideoLAN's x264 mirror.
# Deliberately avoid opaque prebuilt packages without complete corresponding source.
set -euo pipefail
FFMPEG_COMMIT=f46e514491172d15bd74b4abb1814cd2f05a763e
X264_COMMIT=c24e06c2e184345ceb33eb20a15d1024d9fd3497
root="$PWD"
prefix="$root/vendor/ffmpeg"
mkdir -p "$prefix/bin" "$prefix/sources" "$prefix/licenses" "$root/build/media"
export PKG_CONFIG_PATH="$prefix/lib/pkgconfig"
export PATH="/mingw64/bin:/usr/bin:$PATH"
for project in ffmpeg x264; do
    if [[ "$project" == ffmpeg ]]; then
        remote=https://github.com/FFmpeg/FFmpeg.git
        revision="$FFMPEG_COMMIT"
    else
        remote=https://github.com/mirror/x264.git
        revision="$X264_COMMIT"
    fi
    git init "$root/build/media/$project"
    current_remote=$(git -C "$root/build/media/$project" config --get remote.origin.url || true)
    if [[ -z "$current_remote" ]]; then
        git -C "$root/build/media/$project" remote add origin "$remote"
    elif [[ "$current_remote" != "$remote" ]]; then
        echo "Unexpected existing source remote for $project; preserving checkout" >&2
        exit 1
    fi
    git -C "$root/build/media/$project" diff --quiet
    git -C "$root/build/media/$project" diff --cached --quiet
    git -C "$root/build/media/$project" fetch --depth 1 origin "$revision"
    git -C "$root/build/media/$project" checkout --detach FETCH_HEAD
    test "$(git -C "$root/build/media/$project" rev-parse HEAD)" = "$revision"
    git -C "$root/build/media/$project" archive --format=tar --prefix="$project/" HEAD | gzip -n > "$prefix/sources/$project-$revision.tar.gz"
done
cd "$root/build/media/x264"
./configure --prefix="$prefix" --enable-static --disable-cli --disable-opencl --extra-ldflags=-static
make -j2
make install
cp COPYING "$prefix/licenses/x264-COPYING.txt"
cd "$root/build/media/ffmpeg"
./configure --prefix="$prefix" --target-os=mingw32 --arch=x86_64 --cc=gcc --cxx=g++ \
    --disable-autodetect --disable-shared --enable-static --disable-debug --disable-doc \
    --disable-network --enable-gpl --enable-libx264 --extra-ldflags=-static
make -j2
make install
cp COPYING.GPLv2 COPYING.GPLv3 LICENSE.md "$prefix/licenses/"
cp ffbuild/config.log "$prefix/sources/ffmpeg-config.log"
cp "$root/packaging/build_ffmpeg.sh" "$prefix/sources/"
gcc --version > "$prefix/sources/toolchain.txt"
"$prefix/bin/ffmpeg.exe" -version > "$prefix/sources/build-version.txt"
"$prefix/bin/ffmpeg.exe" -hide_banner -encoders > "$prefix/sources/encoders.txt"
grep -q libx264 "$prefix/sources/encoders.txt"
grep -q ' aac ' "$prefix/sources/encoders.txt"

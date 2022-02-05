#!/bin/bash
script_file=`readlink -f "$0"`
script_dir=`dirname "$script_file"`


function venv_export_archive() {

    version=`cat $script_dir/../setup.py | perl -n -e"/version='(\d+\.\d+)'/ && print \\\$1"`
    local outdir="$1"
    local srcdir=`readlink -f "$script_dir/.."`
    local prefix=`basename $srcdir`
    local format='tar.gz'
    local outfile="$outdir/$prefix-$version.$format"
    if [ -f "$script_dir/../.git" ]; then
        local ref='refs/remotes/origin/master'
        if [ -f "$script_dir/../.git/refs/heads/master" ]; then
            ref='refs/heads/master'
        fi
        git -C "$script_dir/.." archive --format=$format --prefix=$prefix/ -o "$outfile" "$ref"
    else
        local fname=`basename "$srcdir"`
        tar cfz "$outfile" -C "$srcdir/.." "$fname"
    fi
}

function docker_build_wheel() {

    local package="$1"
    local depends="$2"
    local url="$3"
    local tmpdir=`mktemp -d`
    local dockerfile="$tmpdir/Dockerfile"
    local build_sh="$tmpdir/build.sh"
    #local from_tag='3-slim'
    local from_tag='2-slim'
    #local python_dev_pkg='python3-dev'
    local python_dev_pkg='python-dev'
    #local from_tag='2-alpine'
    local build_image_name="python2-build-wheel:$from_tag"
    local wheel_dir="$script_dir/wheel"
    local existing=''

    if [ -d "$wheel_dir" ]; then
        existing=`find "$wheel_dir" -type f -name "${package}*.whl"`
    fi

    if [ ! -z "$existing" ]; then
        return 0
    fi

    cat > "$dockerfile" <<EOF
ARG TAG=$from_tag
FROM python:\$TAG
RUN apt update -y && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
        build-essential $python_dev_pkg \
        && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
EOF

    docker build --tag "$build_image_name" --build-arg TAG=$from_tag "$tmpdir" || return 1

    if [ ! -z "$depends" ]; then

        deb_depends=''
        wheel_depends=''
        for a in $depends; do
            prefix="${a%:*}"
            wheel_name="${a##*:}"
            if [ "$prefix" == 'wheel' ]; then
                wheel_depends="$wheel_depends $wheel_name"
            else
                deb_depends="$deb_depends $a"
            fi
        done
        cat > "$dockerfile" <<EOF
FROM $build_image_name
EOF
        if [ ! -z "$deb_depends" ]; then
            cat >> "$dockerfile" <<EOF
RUN apt update -y && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
        $deb_depends \
        && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
EOF
        fi
        if [ ! -z "$wheel_depends" ]; then
            echo "RUN pip install $wheel_depends" >> "$dockerfile"
#            echo "RUN echo \"install wheels $wheel_depends\" && \\" >> "$dockerfile"
#            for a in $wheel_depends; do
#                echo "    pip wheel /wheel/${a}*.whl && \\" >> "$dockerfile"
#            done
#            echo "    echo \"done\"" >> "$dockerfile"
        fi
        build_image_name="python-build-wheel-$package:$from_tag"
        docker build --tag "$build_image_name" --build-arg TAG=$from_tag "$tmpdir" || return 1
    fi

    if [ ! -z "$url" ]; then
        cat > "$build_sh" <<EOF
cd /tmp
pip wheel "$url" --wheel-dir /src
EOF
    else
        cat > "$build_sh" <<EOF
cd /tmp
pip wheel $package --wheel-dir /src
EOF
    fi

    docker run --rm -v "$tmpdir:/src" "$build_image_name" '/bin/sh' -x '/src/build.sh' || return 1

    [ ! -d "$wheel_dir" ] && mkdir -p "$wheel_dir"
    find "$tmpdir" -name '*.whl' -exec cp {} "$wheel_dir" \;

    # Remove temp dir
    rm -rf "$tmpdir"
}

function venv_build_wheels() {
    docker_build_wheel 'six' || return 1
    docker_build_wheel 'rfc6555' || return 1
    #docker_build_wheel 'offlineimap' 'wheel:six wheel:rfc6555' 'https://github.com/OfflineIMAP/offlineimap3/archive/master.zip' || return 1
    docker_build_wheel 'offlineimap' 'wheel:six wheel:rfc6555' || return 1
    return 0
}


function venv_build_docker() {
    local build_image="$1"
    local app_binary_depends="$2"
    local app_use_mssql="$3"
    local app_use_mysql="$4"
    #local from_tag='3-alpine'
    #local from_tag='3-slim'
    local from_tag='2-slim'
    local tag='latest'
    local tar_compress_fmt='xz'
    local tar_compress_cmd='xz --threads=2 -z'
    #local tar_compress_fmt='bz2'
    #local tar_compress_cmd='bzip2 -c'
    #local tar_compress_fmt='gz'
    #local tar_compress_cmd='gzip -c'
    local tmpdir=`mktemp -d`
    local dockerfile="$tmpdir/Dockerfile"
    local srcdir=`readlink -f "$script_dir/.."`
    local appname=`basename $srcdir`
    local remove_image_after_build="$build_image"

    venv_build_wheels || return 1

    #venv_export_archive "$tmpdir" || return 1

    [ ! -d "$script_dir/wheel" ] && mkdir "$script_dir/wheel"
    [ ! -d "$script_dir/dpkg" ] && mkdir "$script_dir/dpkg"
    local no_wheels='#'
    local num_wheels=`ls -1 "$script_dir/wheel" | wc -l`
    if [ $num_wheels -ne 0 ]; then
        find "$script_dir/wheel" -type f -exec cp {} "$tmpdir" \;
        no_wheels=''
    fi

    local no_debian_pkgs='#'
    local num_debian_pkgs=`ls -1 "$script_dir/dpkg" | wc -l`
    if [ $num_debian_pkgs -ne 0 ]; then
        find "$script_dir/dpkg" -type f -exec cp {} "$tmpdir" \;
        no_debian_pkgs=''
    fi

    cp -a "$script_dir/app" "$tmpdir/app"

    cat > "$dockerfile" <<EOF
ARG TAG=$from_tag
FROM python:\$TAG
COPY app/*.py /app/
${no_wheels}ADD *.whl /tmp/wheel/
${no_debian_pkgs}ADD *.deb /tmp/dpkg/
RUN test ! -d /tmp/wheel && mkdir -p /tmp/wheel ; \
    find /tmp/wheel -type f -print -exec pip install {} \; && \
    rm -rf /tmp/wheel && \
    rm -rf /usr/share/doc/* /usr/share/man/* /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/log/apt* /var/log/dpkg.log /var/cache/debconf/* && \
    echo "#!/bin/sh\npython /app/arsoft-imapsync.py \\\$@\n" > /usr/local/bin/arsoft-imapsync && \
    chmod +x /usr/local/bin/arsoft-imapsync && \
    useradd -ms /bin/bash app && \
    install -d -g app -o app -m 0755 /etc/arsoft/imapsync && \
    install -d -g app -o app -m 0755 /var/tmp/arsoft-imapsync
USER app
CMD arsoft-imapsync
EOF

    docker build --tag arsoft-imapsync:latest "$tmpdir" || return 1
    docker tag arsoft-imapsync:latest rothan/arsoft-imapsync:latest
    docker push rothan/arsoft-imapsync:latest

    # Remove temp dir
    rm -rf "$tmpdir"
}

venv_build_docker "$venv_docker_image" "$venv_docker_binary_depends" "$venv_docker_use_mssql" "$venv_docker_use_mysql"

exit 0


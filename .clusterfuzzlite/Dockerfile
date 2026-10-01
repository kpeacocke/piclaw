FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:79cc75a68ab65120da54f35d53f10c7536554ffe684eea5bae078a9a5ff82923

COPY . $SRC/piclaw
WORKDIR $SRC/piclaw
COPY .clusterfuzzlite/build.sh $SRC/build.sh
RUN chmod +x $SRC/build.sh

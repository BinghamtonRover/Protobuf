import "dart:io";

/// The executable to run.
const command = "protoc";

/// The arguments to pass.
const args = ["--dart_out=generated", "-I", "Protobuf", "Protobuf/*.proto"];

void main() => Process.run(command, args);

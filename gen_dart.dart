// ignore_for_file: avoid_print

import "dart:io";

Future<void> checkProtoc() async {
  const command = "protoc";
  const args = ["--help"];
  try {
    await Process.run(command, args);
  } on ProcessException {
    print("\nError: Could not find protoc. Please download it from the URL below and add it to your PATH");
    print("https://github.com/protocolbuffers/protobuf/releases/latest");
    exit(1);  // could not find protoc
  }
}

Future<bool> hasProtocPlugin() async {
  const command = "dart";
  const args = ["pub", "global", "list"];
  final result = await Process.run(command, args);
  return result.stdout.contains("protoc_plugin");
}

Future<void> installDartPlugin() async {
  const command = "dart";
  const args = ["pub", "global", "activate", "protoc_plugin"];
  final result = await Process.run(command, args);
  if (result.exitCode != 0) {
    print("\nError: Could not install protoc_plugin from Pub");
    print("Tried running: $command ${args.join(' ')}");
    exit(2);  // could not install protoc_plugin
  }
}

Future<void> generateProtobuf() async {
  const command = "protoc";
  const args = ["--dart_out=lib/src/generated", "-I", "Protobuf", "Protobuf/*.proto", "google/protobuf/timestamp.proto"];
  final result = await Process.run(command, args);
  if (result.exitCode != 0) {
    print("\nError: Could not generate Protobuf");
    print(result.stderr);
    exit(3);  // could not generate Protobuf
  }
}

void main() async {
  print("Checking for protoc...");
  await checkProtoc();

  if (!await hasProtocPlugin()) {
    print("Installing Dart plugin...");
    await installDartPlugin();
  }

  print("Generating Protobuf...");
  await generateProtobuf();

  print("Done!");
}

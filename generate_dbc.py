from math import ceil
from pathlib import Path
import cantools
import yaml
import os
from argparse import ArgumentParser

# Inspiration taken from UW Robotics database generator:
# https://github.com/uwrobotics/uwrt_mars_rover_hw_bridge/blob/master/scripts/generate_can.py


# CAN ID class used to preserve hex format of ID values
class CAN_ID(int):
    pass


def hexint_representer(dumper, data):
    return yaml.ScalarNode("tag:yaml.org,2002:int", hex(data))


def yaml_to_message(
    message_name: str,
    message: dict[str, object],
    type_aliases: dict[str, object],
) -> cantools.database.can.Message:
    """
    Converts a YAML object into a cantools database message
    """
    # Define a list of signals for the CAN message
    signals: list[cantools.database.can.Signal] = []

    # Keep track of and auto increment the start bit for each signal
    start_bit = 0

    for signal in message["signals"]:
        signal_name = list(signal.keys())[0]
        signal = signal[signal_name]

        if "type_alias" in signal:
            alias_name = signal["type_alias"]
            if not alias_name in type_aliases:
                print(
                    f'Unknown type alias "{alias_name}" in message "{message_name}", signal "{signal_name}"'
                )
                exit()

            signal = {**type_aliases[alias_name], **signal}

        length = signal["length"]
        is_signed = signal["is_signed"]

        # If both scale/offset and min/max were given, we don't need to calculate anything
        if (
            "scale" in signal
            and "offset" in signal
            and "min" in signal
            and "max" in signal
        ):
            scale = signal["scale"]
            offset = signal["offset"]
            sig_min = signal["min"]
            sig_max = signal["max"]
        # If we are only given scale and offset, calculate the min and max
        elif "scale" in signal and "offset" in signal:
            scale = signal["scale"]
            offset = signal["offset"]

            # Calculate the min and max based off the scale and offset
            sig_min = (
                -((2 ** (length - 1) - 1) * scale + offset) if is_signed else offset
            )
            sig_max = (
                (2 ** (length - 1) - 1) * scale + offset
                if is_signed
                else (2**length - 2) * scale + offset
            )
        # If we are only given min and max, calculate scale and/or offset
        elif "min" in signal and "max" in signal:
            sig_min = signal["min"]
            sig_max = signal["max"]

            # Calculate the scale and offset based on min/max and length
            scale = (sig_max - sig_min) / (2**length - 2)
            offset = sig_min + (2 ** (length - 1) - 1) * scale if is_signed else sig_min
        # Not enough data was provided
        else:
            print(
                'Missing fields for signal "'
                + signal_name
                + '" in message "'
                + message_name
                + '"!'
            )
            print("Supply either signal scale/offset or signal min/max")
            print("Script terminated.")
            exit()

        # Populate optional fields of the signal
        signal["scale"] = scale
        signal["offset"] = offset
        signal["min"] = sig_min
        signal["max"] = sig_max

        signals.append(
            cantools.database.can.Signal(
                name=signal_name,
                start=start_bit,
                length=signal["length"],
                byte_order="little_endian",
                is_signed=signal["is_signed"],
                conversion=cantools.database.conversion.BaseConversion.factory(
                    scale=signal["scale"],
                    offset=signal["offset"],
                    choices=signal["values"] if "values" in signal else None,
                ),
                minimum=signal["min"],
                maximum=signal["max"],
                unit=signal["unit"] if "unit" in signal else None,
                comment=signal["comment"] if "comment" in signal else None,
            )
        )

        start_bit += length

    if not "size" in message or message["size"] == "auto":
        message_size = 0
        for signal in signals:
            message_size += signal.length
        message_size = ceil(message_size / 8)
    else:
        message_size = message["size"]

    is_fd_message: bool = message["is_fd"] if "is_fd" in message else False
    max_size_bytes: int = 64 if is_fd_message else 8

    if message_size > max_size_bytes:
        print(
            f'Message "{message_name}" is too long to fit into {max_size_bytes} bytes!'
        )
        print("Consider splitting into multiple messages!")
        exit()

    return cantools.database.can.Message(
        frame_id=message["id"],
        name=message_name,
        length=message_size,
        signals=signals,
        comment=message["comment"] if "comment" in message else None,
    )


def load_messages_from_file(file_name: str) -> list[cantools.database.can.Message]:
    """
    Load messages from a YAML file with the given file name. Returns a list of CAN database messages.
    """
    with open(file_name) as yaml_file:
        can_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Load the type aliases from the YAML file
    # The type aliases are to make it cleaner and clearer for simple
    # and commonly used types, such as booleans and bool states
    type_aliases: dict[str, dict] = {}

    if "type_aliases" in can_yaml:
        for alias in can_yaml["type_aliases"]:
            alias_name = list(alias.keys())[0]
            alias = alias[alias_name]

            type_aliases[alias_name] = alias

    # Define a list of messages loaded from the YAML file, which will be
    # put into a DBC file
    messages: list[cantools.database.can.Message] = []

    # Loop through each message defined in the YAML file, and convert them into a cantools
    # database message
    for message in can_yaml["messages"]:
        message_name = list(message.keys())[0]
        message = message[message_name]

        # change value in "id:" section to hex
        message["id"] = CAN_ID(message["id"])

        messages.append(yaml_to_message(message_name, message, type_aliases))

    return messages


def main():
    # Make sure we are in the correct directory
    script_path = Path(__file__).resolve().parent
    os.chdir(script_path)

    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="rover.dbc",
        help="Output of the generated DBC file.",
    )
    args = arg_parser.parse_args()

    yaml.add_representer(CAN_ID, hexint_representer)

    messages = load_messages_from_file("can_messages.yaml")

    can_db = cantools.database.can.Database(
        messages=messages,
        version="1.0.0",
    )

    cantools.database.dump_file(
        can_db,
        args.output,
        sort_signals=cantools.database.utils.sort_signals_by_start_bit,
        database_format="dbc",
    )
    print("Successfully generated DBC")


if __name__ == "__main__":
    main()

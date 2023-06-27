# Covert SMS Program

This is the README file for the Covert SMS program. The program is designed to run on a Raspberry Pi (version 3 or higher) with a SIM7600X 4G HAT installed. It provides functionality to send and receive SMS messages, retrieve GPS position, and manage saved messages. This is a work in progress.

## Prerequisites

To run the Covert SMS program, you need the following:

- Raspberry Pi (version 3 or higher)
- SIM7600X 4G HAT installed on the Raspberry Pi
- Python 3 installed on the Raspberry Pi
- RPi.GPIO library installed (can be installed using `pip install RPi.GPIO`)
- Serial library installed (can be installed using `pip install serial`)

## Getting Started

1. Connect the SIM7600X 4G HAT to the Raspberry Pi.
2. Make sure the Raspberry Pi is powered on.
3. Open a terminal and navigate to the directory where the Covert SMS program script is located.

## Configuration

Before running the Covert SMS program, you need to configure the `config.ini` file with your specific values. Follow these steps:

1. Locate the `config.ini` file in the repository.
2. Open `config.ini` in a text editor.
3. Replace the default values in `config.ini` with your specific configuration details.
4. Save the `config.ini` file.

**Note:** It is important to provide accurate and valid values in the `config.ini` file for the program to function correctly. Make sure to update all the required entries.

## Usage

To run the Covert SMS program, execute the following command in the terminal:

```shell
python covert_sms.py
```

Once the program starts, it will automatically parse the `config.ini` file and check if any values are still set to their default values. If any value is not updated, an error message will be displayed, and the program will exit. You will be prompted to update the `config.ini` file with the required values.

Follow the instructions in the error message and update the `config.ini` file accordingly. Once you have updated the file, you can rerun the program.

**Note:** The Covert SMS program assumes that you have the correct hardware setup and the SIM7600X HAT is properly initialized. Make sure to refer to the documentation of your hardware for the correct setup instructions.

## Troubleshooting

If you encounter any issues while running the Covert SMS program, consider the following:

- Ensure that the SIM7600X HAT is properly connected to the Raspberry Pi.
- Verify that the required libraries (`RPi.GPIO` and `serial`) are installed.
- Check that the serial port is correctly assigned in the script. Modify the Serial_Device entry in the config.ini file to match the serial port assigned to your SIM7600X HAT device. For example, if your device is assigned to /dev/ttyUSB0, update the Serial_Device entry in config.ini to Serial_Device = /dev/ttyUSB0.
- Make sure the SIM7600X HAT is powered on before running the program.

If the problem persists, try restarting the Raspberry Pi and ensuring that the SIM7600X HAT is functioning correctly.

## Disclaimer

Please note that the Covert SMS program is designed for a specific use case and assumes a particular hardware configuration. It may not work correctly or as expected in different environments or with different hardware setups. Use it at your own risk and ensure that you understand the implications of using such a program.

## Acknowledgements

The Covert SMS program is built upon the hardware setup guide and the `send_at` function provided by Tim. You can find the hardware setup guide at [4G and GPS HAT For Raspberry Pi - Waveshare SIM7600X](https://core-electronics.com.au/guides/raspberry-pi-4g-gps-hat/) and the original `send_at` function by Tim.


## License

The Covert SMS program is distributed under the [MIT License](https://opensource.org/licenses/MIT). Feel free to modify and distribute it according to your needs.

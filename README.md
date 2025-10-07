# weather-pi

Web visualization of data coming from several weather station.

### Server
The server package is written in Python Flask and allows:
- [x] multiple weather station to upload data
- [x] get last measured data
- [ ] visualize graphs on a given period
- [ ] visualize weather forecast

### Client
As an example of client the provided one uses measurement coming from `rtl_433` which is a software that uses an SDR to sniff traffic coming from several weather station, in the given example I've used a `Bresser 5 in 1` weather station.


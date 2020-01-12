var g_ignore_relay_resp = {}

var g_sunrise_datetime = new Date("1970-01-01T00:00:00");
var g_sun_timer = 0

var g_modem_connected = true
var g_up_mb = 0
var g_down_mb = 0
var g_conn_time = 0

function create_switches()
{
    fetch("relay.json")
        .then(response => response.json())
        .then(data => {
            for (relay_id in data) {
                if (data[relay_id].enabled) {
                    var relay_name = data[relay_id].name;
                    var relays_div = document.getElementById('relays');
                    var title = document.createElement("h2");
                    var name = document.createTextNode(relay_name);
                    title.appendChild(name);
                    var label = document.createElement("label");
                    label.className = "switch";
                    var input = document.createElement("input");
                    input.setAttribute("relay-id",relay_id);
                    input.setAttribute("relay-name",relay_name);
                    input.id = "relay-"+relay_id+"-switch";
                    input.type = "checkbox";
                    input.setAttribute("onclick","change_relay_state(this)");
                    g_ignore_relay_resp[relay_id] = false;
                    var slider = document.createElement("span");
                    slider.className = "slider round";
                    if (data[relay_id].state) {
                          input.checked = true;
                    } else {
                          input.checked = false;
                    }
                    label.appendChild(input);
                    label.appendChild(slider);
                    relays_div.appendChild(title);
                    relays_div.appendChild(label);
                }
            }
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function change_relay_state(elem){

    var data = {};
    var relay_name = elem.getAttribute("relay-name");
    var relay_id = elem.getAttribute("relay-id");
    var relay_state = elem.checked ? 'on' : "off";
    data[relay_name] = relay_state;
    g_ignore_relay_resp[relay_id] = true;
    console.log(data);
    fetch("buttons", {
        method: 'POST',
        body: JSON.stringify(data) })
        .then((response) => response.text())
        .then((data) => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

function get_relay_data()
{
    fetch("relay.json")
        .then(response => response.json())
        .then(data => {
            for (relay_id in data) {
                if (data[relay_id].enabled) {
                    if(!g_ignore_relay_resp[relay_id]) {
                        var relay_switch = document.querySelector("#relay-"+relay_id+"-switch");
                        if (data[relay_id].state) {
                            relay_switch.checked = true;
                        } else {
                            relay_switch.checked = false;
                        }
                    } else { g_ignore_relay_resp[relay_id] = false; }
                }
            }
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function get_v_data()
{
    fetch("stats_ajax.json")
        .then(response => response.json())
        .then(data => {
            document.querySelector("#battery-voltage").innerHTML = Number(data.bv).toFixed(2) + "V"
            var battery_icon = document.querySelector("#battery-charge-icon")
            if(data.bcs == "Fault") {
                battery_icon.src= "/icon/battery_missing.png"
            } else if(data.bcs != "Not charging") {
                battery_icon.src= "/icon/battery_charging.png"
            } else if(data.bsoc > 95) {
                battery_icon.src= "/icon/battery_4.png"
            } else if(data.bsoc > 80) {
                battery_icon.src= "/icon/battery_3.png"
            } else if(data.bsoc > 60) {
                battery_icon.src= "/icon/battery_2.png"
            } else if(data.bsoc > 40) {
                battery_icon.src= "/icon/battery_1.png"
            } else if(data.bsoc > 0) {
                battery_icon.src= "/icon/battery_0.png"
            } else {
                battery_icon.src= "/icon/battery_missing.png"
            }
            document.querySelector("#battery-current").innerHTML = Number(data.bi).toFixed(2) + "A"
            document.querySelector("#battery-cs").innerHTML = data.bcs + ": " + data.bsoc + "%"
            document.querySelector("#pv-power").innerHTML = data.pvp + "W"
            document.querySelector("#pv-voltage").innerHTML = data.pvv + "V"
            document.querySelector("#pv-mppt").innerHTML = data.pvmppt
            document.querySelector("#pv-yield").innerHTML = data.pvy + "Wh"
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function seconds2time (seconds) {
    var days    = Math.floor(seconds / 86400);
    var hours   = Math.floor((seconds - (days * 86400)) / 3600);
    var minutes = Math.floor((seconds - (days * 86400) - (hours * 3600)) / 60);
    var seconds = seconds - (days * 86400) - (hours * 3600) - (minutes * 60);
    var time = "";

    if (days != 0) {
      time = days+" days ";
    }
    if (hours != 0 || time !== "") {
      hours = (hours < 10 && time !== "") ? "0"+hours : String(hours);
      time += hours+":";
    }
    if (minutes != 0 || time !== "") {
      minutes = (minutes < 10 && time !== "") ? "0"+minutes : String(minutes);
      time += minutes+":";
    }
    if (time === "") {
      time = seconds+"s";
    }
    else {
      time += (seconds < 10) ? "0"+seconds : String(seconds);
    }
    return time;
}

function get_m_data()
{
    fetch("modem.json")
        .then(response => response.json())
        .then(data => {
            var lte_ssi = document.createElement("img");
            lte_ssi.id = "lte-ssi"
            lte_ssi.className = "icon-large-left"
            lte_ssi.src = "/icon/signal_"+data.signal_strength+".png";
            var lte_net_type = document.createTextNode(data.network_type);
            var lte_title = document.querySelector("#lte-net-type");
            lte_title.innerHTML= "";
            lte_title.appendChild(lte_ssi);
            lte_title.appendChild(lte_net_type);
            g_up_mb = (data.data_usage.data_up /(1024*1024)).toFixed(2);
            g_down_mb = (data.data_usage.data_down /(1024*1024)).toFixed(2);
            var rate_up_kb = (data.data_usage.data_rate_up /1024).toFixed(2);
            var rate_down_kb = (data.data_usage.data_rate_down /1024).toFixed(2);
            var total_up_gb = (data.data_usage.data_total_up /(1024*1024*1024)).toFixed(2);
            var total_down_gb = (data.data_usage.data_total_down /(1024*1024*1024)).toFixed(2);
            var total_data_percent =  (((data.data_usage.data_total_up + data.data_usage.data_total_down) / (24 * 1024 * 1024 * 1024)) * 100).toFixed(1);
            g_modem_connected = data.connected;
            if(g_modem_connected) {
                if(g_conn_time %60 == 0) {
                    g_conn_time = data.connected_time;
                    document.querySelector("#lte-data").innerHTML = "Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time);
                }
                document.querySelector("#lte-rate").innerHTML = "Speed: "+rate_down_kb+"kB/s / "+rate_up_kb+"kB/s";
            } else {
                document.querySelector("#lte-data").innerHTML = "Not Connected!";
                document.querySelector("#lte-rate").innerHTML = "";
            }
            document.querySelector("#lte-total-data").innerHTML = "Total: "+total_down_gb+"GB / "+total_up_gb+"GB - "+total_data_percent+"% of 24GB";
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function update_conn_time()
{
    g_conn_time++;
    if(g_modem_connected) {
        document.querySelector("#lte-data").innerHTML = "Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time);
    } else {
        document.querySelector("#lte-data").innerHTML = "Not Connected!";
    }
}

function get_env_data()
{
    fetch("bme.json")
        .then(response => response.json())
        .then(data => {
// Now fed from weather data
//            document.querySelector(".env #t").innerHTML = data.t + String.fromCharCode(176) + "C"
            document.querySelector("#pressure").innerHTML = data.p + "mb"
            document.querySelector("#humidity").innerHTML = data.h + "%"
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function get_sun_data()
{
    fetch("sun.json")
        .then(response => response.json())
        .then(data => {
            if(data.state == "day") {
                document.querySelector("#pv-mppt-icon").src = "/icon/solar_panel_sun.png"
            } else {
                document.querySelector("#pv-mppt-icon").src = "/icon/solar_panel.png"
            }
            document.querySelector("#sunrise-time").innerHTML = data.sunrise.slice(11, 16)
            g_sunrise_datetime = new Date(data.sunrise)
            document.querySelector("#sunset-time").innerHTML = data.sunset.slice(11, 16)
            document.querySelector("#solar-elevation").innerHTML = data.solar_elevation + String.fromCharCode(176)
            if(data.time_to_sunrise > 0) {
                document.querySelector("#sun-timer-icon").src = "/icon/sunrise.png";
                g_sun_timer = data.time_to_sunrise
            } else {
                document.querySelector(".pv #sun-timer-icon").src = "/icon/sunset.png";
                g_sun_timer = data.time_to_sunset
            }
            document.querySelector(".pv #sun-timer").innerHTML = seconds2time(g_sun_timer)
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function update_sun_timer()
{
    g_sun_timer--;
    var current_datetime = new Date()
    if(g_sunrise_datetime.getDay() != current_datetime.getDay()) {
        get_sun_data();
    } else if(g_sun_timer < 0) {
        get_sun_data();
    } else {
        document.querySelector("#sun-timer").innerHTML = seconds2time(g_sun_timer);
    }
}

function get_weather_data()
{
    fetch("weather.json")
        .then(response => response.json())
        .then(data => {
            document.querySelector("#temperature").innerHTML = data.current.temperature.toFixed(1) + String.fromCharCode(176) + "C"
            document.querySelector("#weather-type-icon").src = "/icon/weather/"+data.hour.icon+".png";
            document.querySelector("#weather-type-icon").title = data.day.summary;
            document.querySelector("#weather-type-text").innerHTML = data.hour.summary
            var wind_icon = ""
            if (data.current.wind_speed == 0) {
                wind_icon = "wind0.png";
            } else if (data.current.wind_speed < 3) {
                wind_icon = "wind1.png";
            } else if (data.current.wind_speed < 63) {
                wind_icon = "wind"+(Math.round(data.current.wind_speed / 5)*5)+".png";
            } else if (data.current.wind_speed < 98) {
                wind_icon = "wind60.png";
            } else if (data.current.wind_speed < 108) {
                wind_icon = "wind"+(Math.round(data.current.wind_speed / 5)*5)+".png";
            } else {
               // We're in serious trouble if the wind is > 107mph...
                wind_icon = "wind105.png";
            }
            document.querySelector("#wind-direction").src = "/icon/wind/"+wind_icon;
            var style_string = `
                -webkit-transform: rotate(`+data.current.wind_bearing+`deg);
                -moz-transform: rotate(`+data.current.wind_bearing+`deg);
                -o-transform: rotate(`+data.current.wind_bearing+`deg);
                -ms-transform: rotate(`+data.current.wind_bearing+`deg);
                transform: rotate(`+data.current.wind_bearing+`deg);
            `;
            document.querySelector("#wind-direction").style = style_string;
            document.querySelector("#wind-speed").innerHTML = Math.round(data.current.wind_speed)+" mph";
            document.querySelector("#precipitation-chance").innerHTML = data.hour.precip_probability+"%";
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function get_river_data()
{
    fetch("river.json")
        .then(response => response.json())
        .then(data => {
            var river_icon = document.createElement("img");
            river_icon.id = "river-icon"
            river_icon.className = "icon-large-left"
            river_icon.src = "/icon/river.png";
            var river_name = document.createTextNode(data.name);
            var river_title = document.querySelector("#river-name")
            river_title.innerHTML= "";
            river_title.appendChild(river_icon);
            river_title.appendChild(river_name);
            var river_warning = document.createElement("img");
            river_warning.id = "river-warning"
            river_warning.className = "icon-large-right"
            if (data.level > data.high_warn) {
                river_warning.src = "/icon/alert.png";
                river_title.appendChild(river_warning);
            } else if (data.level > data.high) {
                river_warning.src = "/icon/warning.png";
                river_title.appendChild(river_warning);
            }
            var river_status = document.createElement("img");
            river_status.id = "river-status"
            river_status.className = "icon-large-right"
            if (data.status =="rising") {
                river_status.src = "/icon/arrow_up.png";
                river_title.appendChild(river_status);
            } else if (data.status =="falling") {
                river_status.src = "/icon/arrow_down.png";
                river_title.appendChild(river_status);
            }
            document.querySelector("#river-level").innerHTML = "Current level: " + data.level + "m @ "+data.timestamp
            document.querySelector("#river-last-high").innerHTML = "Last high: " + data.last_high_level + "m @ "+data.last_high
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

document.addEventListener('DOMContentLoaded', function()
{
    get_env_data();
    get_v_data();
    create_switches();
    get_m_data();
    get_river_data();
    get_sun_data();
    get_weather_data();

    var counter = 0;
    var i = setInterval(function ()
    {
        get_relay_data();
        update_sun_timer();
        update_conn_time();
        counter++;
        if(counter%3 == 0) {
            get_v_data();
            get_m_data();
        }
        if(counter==300) {
            counter=0;
            get_env_data();
            get_river_data();
            get_weather_data();
        }
    }, 1000);
}, false);

window.onfocus = function() {
    get_v_data();
    get_env_data();
    get_m_data();
    get_river_data();
    get_sun_data();
    get_weather_data();
}

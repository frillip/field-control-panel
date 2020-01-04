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
            for (relay in data) {
                if (data[relay].enabled == true) {
                    var relay_name = data[relay].name;
                    var relays_div = document.getElementById('relays');
                    var title = document.createElement("h2");
                    var name = document.createTextNode(relay_name);
                    title.appendChild(name);
                    var label = document.createElement("label");
                    label.className = "switch";
                    var input = document.createElement("input");
                    input.setAttribute("relay_id",relay);
                    input.setAttribute("relay_name",relay_name);
                    input.id = "relay_"+relay+"_switch";
                    input.type = "checkbox";
                    input.setAttribute("onclick","change_relay_state(this)");
                    g_ignore_relay_resp[relay] = false;
                    var slider = document.createElement("span");
                    slider.className = "slider round";
                    if (data[relay].state) {
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
    var relay_name = elem.getAttribute("relay_name");
    var relay_id = elem.getAttribute("relay_id");
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
            for (relay in data) {
                if (relay != "e") {
                    if(!g_ignore_relay_resp[relay]) {
                        var relay_switch = document.querySelector("#relay_"+relay+"_switch");
                        if (data[relay].state) {
                            relay_switch.checked = true;
                        } else {
                            relay_switch.checked = false;
                        }
                    } else { g_ignore_relay_resp[relay] = false; }
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
            document.querySelector(".battery #voltage").innerHTML = Number(data.bv).toFixed(2) + "V"
            document.querySelector(".battery #current").innerHTML = Number(data.bi).toFixed(2) + "A"
            document.querySelector(".battery #cs").innerHTML = data.bcs + ": " + data.bsoc + "%"
            document.querySelector(".pv #power").innerHTML = data.pvp + "W"
            document.querySelector(".pv #voltage").innerHTML = data.pvv + "V"
            document.querySelector(".pv #mppt").innerHTML = data.pvmppt
            document.querySelector(".pv #yield").innerHTML = data.pvy + "Wh"
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
            document.querySelector(".lte #net").innerHTML = '<img id="ssi" src="" />' +data.network_type;
            document.querySelector(".lte #ssi").src = "/icon/signal_"+data.signal_strength+".png";
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
                    document.querySelector(".lte #data").innerHTML = "Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time);
                }
                document.querySelector(".lte #rate").innerHTML = "Speed: "+rate_down_kb+"kB/s / "+rate_up_kb+"kB/s";
            } else {
                document.querySelector(".lte #data").innerHTML = "Not Connected!";
                document.querySelector(".lte #rate").innerHTML = "";
            }
            document.querySelector(".lte #total_data").innerHTML = "Total: "+total_down_gb+"GB / "+total_up_gb+"GB - "+total_data_percent+"% of 24GB";
        }).catch(error => {
            console.log(error);
            // on error, stop execution
        });
}

function update_conn_time()
{
    g_conn_time++;
    if(g_modem_connected) {
        document.querySelector(".lte #data").innerHTML = "Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time);
    } else {
        document.querySelector(".lte #data").innerHTML = "Not Connected!";
    }
}

function get_env_data()
{
    fetch("bme.json")
        .then(response => response.json())
        .then(data => {
            document.querySelector(".env #t").innerHTML = data.t + String.fromCharCode(176) + "C"
            document.querySelector(".env #p").innerHTML = data.p + "mb"
            document.querySelector(".env #h").innerHTML = data.h + "%"
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
                document.querySelector(".pv #pv_mppt_icon").src = "/icon/solar_panel_sun.png"
            } else {
                document.querySelector(".pv #pv_mppt_icon").src = "/icon/solar_panel.png"
            }
            document.querySelector(".pv #sunrise").innerHTML = data.sunrise.slice(11, 16)
            g_sunrise_datetime = new Date(data.sunrise)
            document.querySelector(".pv #sunset").innerHTML = data.sunset.slice(11, 16)
            document.querySelector(".pv #elevation").innerHTML = data.solar_elevation + String.fromCharCode(176)
            if(data.time_to_sunrise > 0) {
                document.querySelector(".pv #sun_timer_icon").src = "/icon/sunrise.png";
                g_sun_timer = data.time_to_sunrise
            } else {
                document.querySelector(".pv #sun_timer_icon").src = "/icon/sunset.png";
                g_sun_timer = data.time_to_sunset
            }
            document.querySelector(".pv #sun_timer").innerHTML = seconds2time(g_sun_timer)
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
        document.querySelector(".pv #sun_timer").innerHTML = seconds2time(g_sun_timer);
    }
}

function get_weather_data()
{
    fetch("weather.json")
        .then(response => response.json())
        .then(data => {
            document.querySelector("#weather_type_icon").src = "/icon/weather/"+data.weather_type+".png";
            document.querySelector("#weather_type_text").innerHTML = data.weather_type_text
            var wind_icon = ""
            if (data.wind_speed == 0) {
                wind_icon = "wind0.png";
            } else if (data.wind_speed < 3) {
                wind_icon = "wind1.png";
            } else if (data.wind_speed < 63) {
                wind_icon = "wind"+(Math.round(data.wind_speed / 5)*5)+".png";
            } else if (data.wind_speed < 98) {
                wind_icon = "wind60.png";
            } else if (data.wind_speed < 108) {
                wind_icon = "wind"+(Math.round(data.wind_speed / 5)*5)+".png";
            } else {
               // We're in serious trouble if the wind is > 107mph...
                wind_icon = "wind105.png";
            }
            document.querySelector("#wind_direction").src = "/icon/wind/"+wind_icon;
            document.querySelector("#wind_direction").className = "wind"+data.wind_direction;
            document.querySelector("#wind_speed").innerHTML = data.wind_speed+" mph";
            document.querySelector("#precipitation_chance").innerHTML = data.precipitation_chance+"%";
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
            document.querySelector(".river #name").innerHTML = '<img id="icon" src="" />' + data.name;
            document.querySelector(".river #icon").src = "/icon/river.png"; // Will change colour based on level in the future
            if (data.level > data.high_warn) {
                document.querySelector(".river #name").innerHTML += '<img id="warn" src="" />';
                document.querySelector(".river #warn").src = "/icon/alert.png";
            } else if (data.level > data.high) {
                document.querySelector(".river #name").innerHTML += '<img id="warn" src="" />';
                document.querySelector(".river #warn").src = "/icon/warning.png";
            }
            if (data.status =="rising") {
                document.querySelector(".river #name").innerHTML += '<img id="status" src="" />';
                document.querySelector(".river #status").src = "/icon/arrow_up.png";
            } else if (data.status =="falling") {
                document.querySelector(".river #name").innerHTML += '<img id="status" src="" />';
                document.querySelector(".river #status").src = "/icon/arrow_down.png";
            }
            document.querySelector(".river #level").innerHTML = "Current level: " + data.level + "m @ "+data.last_reading
            document.querySelector(".river #last_high").innerHTML = "Last high: " + data.last_high_level + "m @ "+data.last_high
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

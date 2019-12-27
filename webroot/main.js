var g_ignore_relay_resp = {}

var g_sun_timer = 0

var g_modem_connected = true
var g_up_mb = 0
var g_down_mb = 0
var g_conn_time = 0

function create_switches()
{
    $.ajax(
    {
        url: 'relay.json',
        dataType: 'json',
        success: function(json)
        {
            for (relay in json) {
                if (relay != "e") {
                    var relay_name = json[relay].name;
                    var relays_div = document.getElementById('relays');
                    var title = document.createElement("h2");
                    var name = document.createTextNode(relay_name);
                    title.appendChild(name);
                    var label = document.createElement("label");
                    label.setAttribute("class","switch");
                    var input = document.createElement("input");
                    input.setAttribute("relay_id",relay);
                    input.setAttribute("relay_name",relay_name);
                    input.id = "relay_"+relay+"_switch";
                    input.type = "checkbox";
                    input.setAttribute("onclick","change_relay_state(this)");
                    g_ignore_relay_resp[relay] = false;
                    var slider = document.createElement("span");
                    slider.setAttribute("class","slider round");
                    if (json[relay].state) {
                          input.setAttribute("checked", true);
                    }
                    label.appendChild(input);
                    label.appendChild(slider);
                    relays_div.appendChild(title);
                    relays_div.appendChild(label);
                }
            }
        },

        error: function ()
        {
            // on error, stop execution
        }
    });

}

function change_relay_state(elem){

    var data = {};
    relay = $(elem).attr("relay_name")
    data[relay] = $(elem).is(':checked') ? "on" : "off";
    g_ignore_relay_resp[$(elem).attr("relay_id")] = true;
    console.log(data);
    $.ajax({
        type: "POST",
        url: "buttons",
        data: data,
    }).done(function(data) {
            console.log(data);
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
    $.ajax(
    {
        url: 'stats_ajax.json',
        dataType: 'json',
        success: function(json)
        {
            $(".battery #voltage").text(json.bv + "V")
            $(".battery #current").text(json.bi + "A")
            $(".battery #cs").text(json.bcs + ": " + json.bsoc + "%")
            $(".pv #voltage").text(json.pvp + "W")
            $(".pv #power").text(json.pvv + "V")
            $(".pv #mppt").text(json.pvmppt)
            $(".pv #yield").text(json.pvy + "Wh")
        },

        error: function ()
        {
            // on error, stop execution
        }
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
    $.ajax(
    {
        url: 'modem.json',
        dataType: 'json',
        success: function(json)
        {
            $(".lte #net").text(json.network_type);
            $(".lte #net").prepend('<img id="ssi" src="" />')
            $(".lte #ssi").attr("src","/icon/signal_"+json.signal_strength+".png");
            g_up_mb = (json.data_usage.data_up /(1024*1024)).toFixed(2);
            g_down_mb = (json.data_usage.data_down /(1024*1024)).toFixed(2);
            var rate_up_kb = (json.data_usage.data_rate_up /1024).toFixed(2);
            var rate_down_kb = (json.data_usage.data_rate_down /1024).toFixed(2);
            var total_up_gb = (json.data_usage.data_total_up /(1024*1024*1024)).toFixed(2);
            var total_down_gb = (json.data_usage.data_total_down /(1024*1024*1024)).toFixed(2);
            var total_data_percent =  (((json.data_usage.data_total_up + json.data_usage.data_total_down) / (24 * 1024 * 1024 * 1024)) * 100).toFixed(1);
            g_modem_connected = json.connected;
            if(g_modem_connected) {
                if(g_conn_time %60 == 0) {
                    g_conn_time = json.connected_time;
                    $(".lte #data").text("Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time));
                }
                $(".lte #rate").text("Speed: "+rate_down_kb+"kB/s / "+rate_up_kb+"kB/s");
            } else {
                $(".lte #data").text("Not Connected!");
                $(".lte #rate").text("");
            }
            $(".lte #total_data").text("Total: "+total_down_gb+"GB / "+total_up_gb+"GB - "+total_data_percent+"% of 24GB");
        },

        error: function ()
        {
            // on error, stop execution
        }
    });
}

function update_conn_time()
{
    g_conn_time++;
    if(g_modem_connected) {
        $(".lte #data").text("Connected: "+g_down_mb+"MB / "+g_up_mb+"MB - "+seconds2time(g_conn_time));
    } else {
        $(".lte #data").text("Not Connected!");
    }
}

function get_env_data()
{
    $.ajax(
    {
        url: 'bme.json',
        dataType: 'json',
        success: function(json)
        {
            $(".env #t").text(json.t + String.fromCharCode(176) + "C")
            $(".env #p").text(json.p + "mb")
            $(".env #h").text(json.h + "%")
        },

        error: function ()
        {
            // on error, stop execution
        }
    });
}

function get_sun_data()
{
    $.ajax(
    {
        url: 'sun.json',
        dataType: 'json',
        success: function(json)
        {
            $(".pv #sunrise").text(json.sunrise.slice(11, 16))
            $(".pv #sunset").text(json.sunset.slice(11, 16))
            $(".pv #elevation").text(json.solar_elevation + String.fromCharCode(176))
            if(json.time_to_sunrise > 0) {
                $(".pv #sun_timer_icon").attr("src","/icon/sunrise.png");
                g_sun_timer = json.time_to_sunrise
            } else {
                $(".pv #sun_timer_icon").attr("src","/icon/sunset.png");
                g_sun_timer = json.time_to_sunset
            }
            $(".pv #sun_timer").text(seconds2time(g_sun_timer))
        },

        error: function ()
        {
            // on error, stop execution
        }
    });
}

function get_weather_data()
{
    $.ajax(
    {
        url: 'weather.json',
        dataType: 'json',
        success: function(json)
        {
            $("#weather_type_icon").attr("src","/icon/weather/"+json.weather_type+".png")
            $("#weather_type_text").text(json.weather_type_text)
            var wind_icon = ""
            if (json.wind_speed == 0) {
                wind_icon = "wind0.png"
            } else if (json.wind_speed < 3) {
                wind_icon = "wind1.png"
            } else if (json.wind_speed < 63) {
                wind_icon = "wind"+(Math.round(json.wind_speed / 5)*5)+".png"
            } else if (json.wind_speed < 98) {
                wind_icon = "wind60.png"
            } else if (json.wind_speed < 108) {
                wind_icon = "wind"+(Math.round(json.wind_speed / 5)*5)+".png"
            } else {
               // We're in serious trouble if the wind is > 107mph...
                wind_icon = "wind105.png"
            }
            $("#wind_direction").attr("src","/icon/wind/"+wind_icon)
            $("#wind_direction").attr("class","wind"+json.wind_direction)
            $("#wind_speed").text(json.wind_speed+" mph")
            $("#precipitation_chance").text(json.precipitation_chance+"%")
        },

        error: function ()
        {
            // on error, stop execution
        }
    });
}

function update_sun_timer()
{
    g_sun_timer--;
    if(g_sun_timer < 0) {
        get_sun_data();
    } else {
        $(".pv #sun_timer").text(seconds2time(g_sun_timer));
    }
}

function get_river_data()
{
    $.ajax(
    {
        url: 'river.json',
        dataType: 'json',
        success: function(json)
        {
            $(".river #name").text(json.name);
            if (json.level > json.high_warn) {
                $(".river #name").append('<img id="warn" src="" />')
                $(".river #warn").attr("src","/icon/alert.png");
            } else if (json.level > json.high) {
                $(".river #name").append('<img id="warn" src="" />')
                $(".river #warn").attr("src","/icon/warning.png");
            }
            if (json.status =="rising") {
                $(".river #name").append('<img id="status" src="" />')
                $(".river #status").attr("src","/icon/arrow_up.png");
            } else if (json.status =="falling") {
                $(".river #name").append('<img id="status" src="" />')
                $(".river #status").attr("src","/icon/arrow_down.png");
            }
            $(".river #name").prepend('<img id="icon" src="" />')
            $(".river #icon").attr("src","/icon/river.png"); // Will change colour based on level in the future
            $(".river #level").text("Current level: " + json.level + "m @ "+json.last_reading)
            $(".river #last_high").text("Last high: " + json.last_high_level + "m @ "+json.last_high)
        },

        error: function ()
        {
            // on error, stop execution
        }
    });
}

$(function ()
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
});

window.onfocus = function() {
    get_v_data();
    get_env_data();
    get_m_data();
    get_river_data();
    get_sun_data();
    get_weather_data();
}

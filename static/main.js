var r1switchElement = $(".switch #fence");
var r2switchElement = $(".switch #cameras");
var r3switchElement = $(".switch #lighting");

function get_r_data()
{
    $.ajax(
    {
        url: 'relay.json',
        dataType: 'json',
        success: function(json)
        {
            if( json[1].state == true ) {
                r1switchElement.prop('checked', 'true');
            } else {
                r1switchElement.prop('checked', false);
            }

            if( json[2].state == true ) {
                r2switchElement.prop('checked', true);
            } else {
                r2switchElement.prop('checked', false);
            }

            if( json[3].state == true ) {
                r3switchElement.prop('checked', true);
            } else {
                r3switchElement.prop('checked', false);
            }
        },

        error: function ()
        {
            // on error, stop execution
        }
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
            $(".lte #ssi").attr("src","/static/signal_"+json.signal_strength+".png");
            var up_mb = (json.data_usage.data_up /(1024*1024)).toFixed(2);
            var down_mb = (json.data_usage.data_down /(1024*1024)).toFixed(2);
            var rate_up_kb = (json.data_usage.data_rate_up /1024).toFixed(2);
            var rate_down_kb = (json.data_usage.data_rate_down /1024).toFixed(2);
            var total_up_gb = (json.data_usage.data_total_up /(1024*1024*1024)).toFixed(2);
            var total_down_gb = (json.data_usage.data_total_down /(1024*1024*1024)).toFixed(2);
            var total_data_percent =  (((json.data_usage.data_total_up + json.data_usage.data_total_down) / (24 * 1024 * 1024 * 1024)) * 100).toFixed(1);
            var conn_time = seconds2time(json.connected_time);
            if(json.connected) {
                $(".lte #data").text("Connected: "+down_mb+"MB / "+up_mb+"MB - "+conn_time);
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

function get_river_data()
{
    $.ajax(
    {
        url: 'river.json',
        dataType: 'json',
        success: function(json)
        {
            $(".river #name").text(json.name);
            $(".river #name").prepend('<img id="icon" src="" />')
            $(".river #icon").attr("src","/static/river.png"); // Will change colour based on level in the future
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
    get_r_data();
    get_m_data();
    get_river_data();

    var counter = 0;
    var i = setInterval(function ()
    {
        get_r_data();
        console.log(counter);
        counter++;
        if(counter%3 == 0) {
            get_v_data();
            get_m_data();
        }
        if(counter==60) {
            counter=0;
            get_env_data();
            get_river_data();
        }
    }, 1000);
});

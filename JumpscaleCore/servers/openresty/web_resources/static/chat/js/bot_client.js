let EXEC_OBJ = {
    "namespace": "default",
    "actor": "chatbot",
    "headers": {
        "response_type": "json"
    },
}


var stringContentGenerate = function (message, kwargs) {
    let contents = ``
    if (typeof kwargs['default'] == 'undefined') {
        contents = `<input type="text" class="form-control" id="value">`
    } else {
        contents = `<input type="text" class="form-control" id="value" value="${kwargs["default"]}"`
    }
    return `
    <h4>${message}</h4>
    <div class="form-group">
        ${contents}
    </div>`
}

var passwordContentGenerate = function (message, kwargs) {
    return `
    <h4>${message}</h4>
    <div class="form-group">
		<input type="password" class="form-control" id="value">
    </div>`
}

var textContentGenerate = function (message, kwargs) {
    return `
    <h4>${message}</h4>
    <div class="form-group">
		<textarea rows="4" cols="50" class="form-control" id="value"></textarea>
    </div>`
}

var intContentGenerate = function (message, kwargs) {
    return `
    <h4>${message}</h4>
    <div class="form-group">
		<input type="number" class="form-control" id="value">
    </div>`
}

var captchaContentGenerate = function (message, captcha, label, kwargs) {
    return `
    <h4>${message}</h4>
    <img src="data:image/png;base64,${captcha}"/>
    <div class="form-group">
        <input type="text" placeholder="Captcha" class="form-control" id="value">
    </div>
    <label class="captcha-error">${label}</label>`
}

var locationContentGenerate = function (message, label, kwargs) {
    return `
    <h4>${message}</h4>
    <div class="form-group">
        <input type="text" placeholder="Location" class="form-control" id="value" readonly>
        <div id="mymap" class="mapdiv" style="width: 60%; height: 300px;">
        <script>
            function locationChoiceGenerate() {
                let lat = 51.260197;
                let lng = 4.402771;

                let mymap = L.map('mymap').setView([lat, lng], 4);

                L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
                    maxZoom: 18,
                    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
                        '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
                        'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                    id: 'mapbox.streets'
                }).addTo(mymap);

                let popup = L.popup();

                function onMapClick(e) {
                    popup
                        .setLatLng(e.latlng)
                        .setContent("You clicked the map at " + e.latlng.toString())
                        .openOn(mymap);
                    sLat = e.latlng['lat'];
                    sLng = e.latlng['lng'];
                    $("#value").val(sLat.toString() + "," + sLng.toString());
                }
                mymap.on('click', onMapClick);
                $('#mymap').on('shown.bs.modal', function () {
                    setTimeout(function () {
                        mymap.invalidateSize();
                    }, 1);
                });
            }
            locationChoiceGenerate();
        </script>
        </div>
    </div>
    <label class="location-error">${label}</label>




    `
}

var mdContentGenerate = function (message, kwargs) {
    let converter = new showdown.Converter({
        tables: true,
        tablesHeaderId: "table"
    });
    const htmlContents = converter.makeHtml(message);
    return `${htmlContents}`;
}

var multiChoiceGenerate = function (message, options, kwargs) {
    let choices = ""
    $.each(options, function (i, value) {
        choices += `
        <div class="items col-xs-5 col-sm-5 col-md-3 col-lg-3">
            <div class="info-block block-info clearfix">
                <div data-toggle="buttons" class="btn-group bizmoduleselect">
                    <label class="btn btn-default">
                        <div class="bizcontent">
                            <input type="checkbox" name="value[]" autocomplete="off" value="${value}">
                            <span class="glyphicon glyphicon-ok glyphicon-lg"></span>
                            <h5>${value}</h5>
                        </div>
                    </label>
                </div>
            </div>
        </div>`;
    });
    let contents = `
    <h4>${message}</h4>
    <div class="form-group">
        <div class="checkbox-container">${choices}</div>
    </div>`;
    return contents;
}

var singleChoiceGenerate = function (message, options, kwargs) {
    let choices = "";
    const classes = ["primary", "success", "danger", "warning", "info"];
    $.each(options, function (i, value) {
        if (i >= classes.length) {
            i -= classes.length;
        }
        choices += `
        <div class="funkyradio-${classes[i]}">
            <input type="radio" name="value" id="${value}" value="${value}"/>
            <label for="${value}">${value}</label>
        </div>`;
    });
    let contents = `
    <h4>${message}</h4>
    <div class="funkyradio">${choices}</div>`;
    return contents;
}

var dropDownChoiceGenerate = function (message, options, kwargs) {
    let choices = "";
    $.each(options, function (i, value) {
        choices += `<option value="${value}">${value}</option>`;
    });
    let contents = `
    <h4>${message}</h4>
    <div class="form-group">
        <select class="form-control" id="value">
            ${choices}
        </select>
    </div>`;
    return contents;
}

var generateSlide = function (res) {
    $("#spinner").toggle();
    // if error: leave the old slide and show the error
    if (res["error"]) {
        $("#error").html(res['error']);
        $(".btn-submit").attr("disabled", "false");
        $(".form-box").toggle({
            "duration": 400
        });
        return
    }
    // If the response contains redirect, so this was the final slide and will take new action
    else if (res['cat'] === "redirect") {
        $(location).attr("href", res["msg"]);
        return
    }
    let contents = "";
    switch (res['cat']) {
        case "string_ask":
            contents = stringContentGenerate(res['msg'], res['kwargs']);
            break;
        case "password_ask":
            contents = passwordContentGenerate(res['msg'], res['kwargs']);
            break;
        case "text_ask":
            contents = textContentGenerate(res['msg'], res['kwargs']);
            break;
        case "int_ask":
            contents = intContentGenerate(res['msg'], res['kwargs']);
            break;
        case "captcha_ask":
            contents = captchaContentGenerate(res['msg'], res['captcha'], res['label'], res['kwargs']);
            break;
        case "md_show":
            contents = mdContentGenerate(res['msg'], res['kwargs']);
            break;
        case "multi_choice":
            contents = multiChoiceGenerate(res['msg'], res['options'], res['kwargs'])
            break;
        case "single_choice":
            contents = singleChoiceGenerate(res['msg'], res['options'], res['kwargs'])
            break;
        case "drop_down_choice":
            contents = dropDownChoiceGenerate(res['msg'], res['options'], res['kwargs'])
            break;
        case "location_ask":
            contents = locationContentGenerate(res['msg'], res['options'], res['kwargs'])
            break
    }
    contents = `
        <fieldset>
            <p id="error" class="red"></p>
			${contents}
			<span class="f1-buttons-right">
				<button type="submit" class="btn btn-submit" required="true">Next</button>
			</span>
		</fieldset>`;
    $("#wizard").html(contents);
    $(".form-box").toggle({
        "duration": 400
    });

    $(".btn-submit").on("click", function (ev) {
        ev.preventDefault();
        let value = "";
        if (["string_ask", "int_ask", "text_ask", "password_ask", "drop_down_choice", "captcha_ask", "location_ask"].includes(res['cat'])) {
            value = $("#value").val();
        } else if (res['cat'] === "single_choice") {
            value = $("input[name='value']:checked").val();
        } else if (res['cat'] === "multi_choice") {
            let values = [];
            $("input[name='value[]']:checked").each(function () {
                values.push($(this).val());
            });
            value = JSON.stringify(values);
        }
        // Validate the input
        const errors = validate(value, res['kwargs']['validate']);
        if (errors.length > 0) {
            var ul = $('<ul>');
            $(errors).each(function (index, error) {
                ul.append($('<li>').html(error));
            });
            $("#error").html(ul);
            $("#error").removeClass("hidden");
            return
        }
        $("#error").addClass("hidden");
        $(this).attr("disabled", "disabled");
        $("#spinner").toggle();
        $(".form-box").toggle({
            "duration": 400
        });
        EXEC_OBJ['command'] = "work_report";
        EXEC_OBJ['args']['result'] = value;
        GEDIS_CLIENT.execute(EXEC_OBJ).then(function (res) {
            EXEC_OBJ['command'] = "work_get";
            delete EXEC_OBJ['args']['result'];
            // Ignore work_report response and wait for getting next question
            GEDIS_CLIENT.execute(EXEC_OBJ).then(function (res) {
                res = JSON.parse(res);
                generateSlide(res);
            });
        });
    });
}



EXEC_OBJ["command"] = "session_new";
// TOPIC is set through etlua template
EXEC_OBJ["args"] = {
    "topic": TOPIC
};
GEDIS_CLIENT.execute(EXEC_OBJ).then(function (res) {
    res = JSON.parse(res);
    EXEC_OBJ['command'] = "work_get";
    EXEC_OBJ['args'] = {
        "sessionid": res['sessionid']
    }
    GEDIS_CLIENT.execute(EXEC_OBJ).then(function (res) {
        res = JSON.parse(res);
        generateSlide(res);
    });
});
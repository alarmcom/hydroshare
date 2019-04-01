function initializeTable() {
    var RESOURCE_TYPE_COL = 0;
    var TITLE_COL = 1;
    var OWNER_COL = 2;
    var DATE_CREATED_COL = 3;
    var LAST_MODIFIED_COL = 4;

    var colDefs = [
        {
            "targets": [RESOURCE_TYPE_COL],     // Resource type
            "width": "10%"
        },
        {
            "targets": [TITLE_COL],     // Resource type
            "width": "20%"
        },
        {
            "targets": [OWNER_COL],     // Resource type
            "width": "10%"
        },
        {
            "targets": [DATE_CREATED_COL]     // Date created
        },
        {
            "targets": [LAST_MODIFIED_COL]     // Last modified
        },
    ];
    /*

    $('#recently-visited-resources').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "ordering": false,
        "lengthChange": false,
        // "order": [[TITLE_COL, "asc"]],

        "columnDefs": colDefs
    });
    */

    $('#recently-visited-resources').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "ordering": false,
        "lengthChange": false,
        // "order": [[TITLE_COL, "asc"]],

        "columnDefs": colDefs,
        ajax: {
            url: "https://jsonplaceholder.typicode.com/todos/1",
            "dataSrc": function (json) {
                let timestamp = 1548997005696;
                let readable_time_ago = get_time_ago_by_timestamp(timestamp);
                let timestamp_2 = "1548997005696";
                let title = "Hurrican Hurvey";
                let readable_time_ago_2 = build_title_HTML_element(title, timestamp_2);
                let author = "David Tarboton";
                let resource_type = "Composite";
                let visibility = "public";

                console.log("success");
                json = [
                    [
                        readable_time_ago,
                        readable_time_ago_2,
                        author,
                        resource_type,
                        visibility,
                    ],

                ];
                return json;
            },
        },
        type: 'GET',
        dataType: 'jsonp',
        headers: {
            'Access-Control-Allow-Origin': '*'
        },
        crossDomain: true,
        xhrFields: {
            withCredentials: false
        }
    });
}

$(document).ready(function () {
    initializeTable();

    $('[data-toggle="DT_popover"]').popover({container: 'body'});
});


function get_resource_url_by_id(id) {
    let url_base = "href=\"/resource/";
    return url_base + id + "\"";
}

function build_title_HTML_element(title, id) {
    return "<a " + get_resource_url_by_id(id) + ">" + title + "</a>";
}

function get_time_ago_by_timestamp(previous) {
    var current = new Date().getTime();
    console.log("time = " + current);

    var msPerMinute = 60 * 1000;
    var msPerHour = msPerMinute * 60;
    var msPerDay = msPerHour * 24;
    var msPerMonth = msPerDay * 30;
    var msPerYear = msPerDay * 365;

    var elapsed = current - previous;

    if (elapsed < msPerMinute) {
        return Math.round(elapsed / 1000) + ' seconds ago';
    } else if (elapsed < msPerHour) {
        return Math.round(elapsed / msPerMinute) + ' minutes ago';
    } else if (elapsed < msPerDay) {
        return Math.round(elapsed / msPerHour) + ' hours ago';
    } else if (elapsed < msPerMonth) {
        return Math.round(elapsed / msPerDay) + ' days ago';
    } else if (elapsed < msPerYear) {
        return Math.round(elapsed / msPerMonth) + ' months ago';
    } else {
        return Math.round(elapsed / msPerYear) + ' years ago';
    }
}



/**
 * based on:
 * https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_sort_table_desc
 * https://www.w3schools.com/howto/howto_js_sort_table.asp
 */
function parse_num(num) {
    var parsed = parseFloat(num.replace(/,/g, ''));
    return parsed;
}

function sort_str(a, b, dir) {
    if (dir == "asc") {
        if (a.innerHTML.toLowerCase() > b.innerHTML.toLowerCase()) {
            return true;
        }
    } else if (dir == "desc") {
        if (a.innerHTML.toLowerCase() < b.innerHTML.toLowerCase()) {
            return true;
        }
    }
    return false;

}

function sort_wc(a, b, dir) {
    if (dir == "asc") {
        if (parse_num(a.innerHTML) > parse_num(b.innerHTML)) {
            return true;
        }
    } else if (dir == "desc") {
        if (parse_num(a.innerHTML) < parse_num(b.innerHTML)) {
            return true;
        }
    }
    return false;
}

function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("word-count-table");
    switching = true;
    //Set the sorting direction to ascending:
    dir = "asc";
    /*Make a loop that will continue until
    no switching has been done:*/
    while (switching) {
        //start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /*Loop through all table rows (except the
        first, which contains table headers):*/
        for (i = 1; i < (rows.length - 2); i++) {
            //start by saying there should be no switching:
            shouldSwitch = false;
            /*Get the two elements you want to compare,
            one from current row and one from the next:*/
            x = rows[i].getElementsByTagName("td")[n];
            y = rows[i + 1].getElementsByTagName("td")[n];
            /*check if the two rows should switch place,
            based on the direction, asc or desc:*/
            if (n == 1) {
                shouldSwitch = sort_str(x, y, dir);
            } else if (n == 0 || n == 3) {
                shouldSwitch = sort_wc(x, y, dir);
            }
            if (shouldSwitch) {
                break;
            }
        }
        if (shouldSwitch) {
            /*If a switch has been marked, make the switch
            and mark that a switch has been done:*/
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            //Each time a switch is done, increase this count by 1:
            switchcount++;
        } else {
            /*If no switching has been done AND the direction is "asc",
            set the direction to "desc" and run the while loop again.*/
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}
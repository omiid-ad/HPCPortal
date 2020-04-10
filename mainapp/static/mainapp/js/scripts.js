function calcCost() {
    var xhttp;
    var cpu = document.getElementById("cpu").value;
    var ram = document.getElementById("ram").value;
    var disk = document.getElementById("disk").value;
    var days = document.getElementById("days").value;
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "/calc_cost?cpu=" + cpu + '&' + "ram=" + ram + '&' + "disk=" + disk + '&' + "days=" + days, true);
    xhttp.send();
    xhttp.onreadystatechange = function () {
        var result = JSON.parse(this.response);
        var total = JSON.parse(result["total"]);
        var expire_date = JSON.parse(result["expire_date"]);
        window.alert(expire_date);
        window.alert(total);
        // document.getElementById("cost").value = total;
        // document.getElementById("expireddate").innerHTML = expire_date;
    }
}

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
        document.getElementById("cost").value = total;
    }
}

function cancelYN(pk) {
    var serial = document.getElementById("serial");
    let msg = "آیا از ارسال درخواست لغو برای سرویس " + serial.innerHTML + " اطمینان دارید؟";
    var conf = window.confirm(msg);

    if (conf === true) {
        var xhttp;
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "/cancel?pk=" + pk, true);
        xhttp.send();
        xhttp.onreadystatechange = function () {
            var result = JSON.parse(this.response);
            var status = JSON.parse(result["status"]);
            if (status == 200) {
                location.reload();
            } else if (status == 201) {
                location.reload();
            }
        }
    }
}

function profileHover() {
    let dd = document.getElementById("navbardrop");
        dd.click();
}
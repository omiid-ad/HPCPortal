function cancelYN(pk) {
    let serId = "serial" + pk.toString();
    let serial = document.getElementById(serId);
    let msg = "آیا از ارسال درخواست لغو برای سرویس " + serial.innerHTML + " اطمینان دارید؟";
    let conf = window.confirm(msg);

    if (conf === true) {
        let xhttp;
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
    const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    if (vw > 576) {
        let dd = document.getElementById("navbardrop");
        dd.click();
    }
}

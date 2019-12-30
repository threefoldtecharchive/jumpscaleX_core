import AnsiUp from "ansi_up";

function formatDate(date) {
    if (typeof date == "number") {
        date = new Date(date * 1000);
    }

    return (
        date.getFullYear() +
        "-" +
        (date.getMonth() + 1) +
        "-" +
        date.getDate() +
        " " +
        date.getHours() +
        ":" +
        date.getMinutes() +
        ":" +
        date.getSeconds()
    );
}


const ansiUp = new AnsiUp();

export { formatDate, ansiUp };

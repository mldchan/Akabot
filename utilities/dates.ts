
export function getToday() {
    let d = new Date();
    d = new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
    return d;
}

import fetch from "node-fetch";
import tf from "@tensorflow/tfjs-node";
import http from "http";
import fs from "fs";
import jpeg from "jpeg-js";
import canvas from "canvas";

var minsize = 10;
var maxsize = 40;
var imgTolerant = 65;
var size = 30;
var hPic = 720;
var wPic = 1280;
var canvFull = canvas.createCanvas(wPic, hPic);
var canv50 = canvas.createCanvas(size, size);

var model = tf.sequential();
var gameId = "";
var pusto = [];
var mask = [];
var listBB = [];
var listClast = [];
var shortListBB = [];
var ctx = canvFull.getContext("2d");
var ctx50 = canv50.getContext("2d");
var mydata;
// var list_ball_BB = [];

var ballCoord = { x: 0, y: 0 };
var oldBallCoord = { x: 0, y: 0 };
var speed = { x: 0, y: 0 };
var playersList = [];
var whileLoop = true;
var minY = 0;
var bc = 0;
var hc = 0;
var fc = 0;
var pauseState = false;
var jsonInput = {};
var myserver;
//Model
async function loadModel(name) {
    model.path = "file://" + name + ".json";
    await tf.loadLayersModel("file://" + name + ".json").then((result) => {
        model = tf.sequential(result);
        compileModel();
    });
}
function compileModel() {
    model.compile({
        optimizer: "adam",
        metrics: ["accuracy"],
        loss: "categoricalCrossentropy",
    });
    console.log("model load and compile");
    model.summary();
}
async function detect(bb, n) {
    ctx50.drawImage(canvFull, bb.x, bb.y, bb.w, bb.h, 0, 0, size, size);
    //var r = tf.image.resizeBilinear(tf.browser.fromPixels(canv50), [size, size]);
    var r = tf.reshape(tf.browser.fromPixels(canv50, 3), [1, size, size, 3]);

    var rez = model.predict(r);
    var dat = await rez.data();
    var m = Math.max(...dat);
    var ii = dat.indexOf(m);
    return { ii, n };
}
function massDetect() {
    var cc = 0;

    for (var i = 0; i < listBB.length; i++) {
        detect(listBB[i], i).then((v) => {
            cc++;
            listBB[v.n].t = v.ii;

            if (v.ii === 2) {
                bc++;
                shortListBB.push(listBB[v.n]);
                if (ballCoord.x == 0 && ballCoord.y == 0) {
                    ballCoord.x = listBB[v.n].xc;
                    ballCoord.y = listBB[v.n].yc;
                }
            }
            if (v.ii === 3) hc++;
            if (v.ii === 4) fc++;
            if (
                v.ii === 2 ||
                v.ii === 3 ||
                v.ii === 4 ||
                listBB[v.n].checkDistans(oldBallCoord.x, oldBallCoord.y, 100)
            ) {
                shortListBB.push(listBB[v.n]);
            }
            if (cc == listBB.length) {
                console.log("found", bc, hc, fc);
                startCheck();
            }
        });
    }
}
//image
function claster() {
    listClast = [];
    for (let k = 0; k < shortListBB.length; k++) {
        const cbb = shortListBB[k];
        var found = false;
        if (cbb.t > 0 && cbb.t != 2) {
            for (let cl = 0; cl < listClast.length; cl++) {
                const cc = listClast[cl];
                if (!(cc.y > cbb.y2 || cc.y2 < cbb.y || cc.x2 < cbb.x || cc.x > cbb.x2)) {
                    cc.x2 = Math.max(cc.x2, cbb.x2);
                    cc.x = Math.min(cc.x, cbb.x);
                    cc.y2 = Math.max(cc.y2, cbb.y2);
                    cc.y = Math.min(cc.y, cbb.y);
                    cc.w = cc.x2 - cc.x;
                    cc.h = cc.y2 - cc.y;

                    if (cc.t == 0) {
                        cc.t = 1;
                    }
                    if (cbb.t == 3) {
                        cc.t += 3;
                    }
                    found = true;
                    break;
                }
            }
            if (!found) {
                var nclast = BB(cbb.x, cbb.y, cbb.w, cbb.h);
                nclast.t = cbb.t == 3 ? 3 : 0;
                listClast.push(nclast);
            }
        }
    }
}
function BB(x, y, w, h) {
    var z = {
        x,
        x2: x + w,
        y2: y + h,
        y,
        w,
        h,
        xc: x + w / 2,
        yc: y + h / 2,
        inBB: (x1, y1) => {
            return !(x1 < x || x1 > x + w || y1 < y || y1 > y + h);
        },
        checkDistans: (xc1, yc1, d) => {
            return Math.abs(x + w / 2 - xc1) < d + w / 2 && Math.abs(y + h / 2 - yc1) < d + h / 2;
        },
        t: -1,
    };

    return z;
}
function readImageFile(path, gray = false) {
    console.log("start load " + path);
    const buf = fs.readFileSync(path);
    const img = jpeg.decode(buf, { formatAsRGBA: true });
    const pixels = img.data;
    const numPixels = img.width * img.height;
    const values = new Uint8Array(numPixels * 3);
    // console.log("==========size=", numPixels, numPixels * 3, numPixels * 4);
    for (let i = 0; i < numPixels; i++) {
        if (gray) {
            values[i * 3] = Math.round((pixels[i * 4] + pixels[i * 4 + 1] + pixels[i * 4 + 2]) / 3);
        } else {
            for (let channel = 0; channel < 3; ++channel) {
                values[i * 3 + channel] = pixels[i * 4 + channel];
            }
        }
    }
    console.log("load img " + path);
    return values;
}
function findMinY() {
    var my = mask.length / 3;
    for (let i = 0; i < my; i++) {
        if (mask[i * 3] > 0) {
            minY = Math.round(i / wPic);
            break;
        }
    }
}
function setPix(ar, i, v) {
    i = Math.max(0, i);
    ar[i] = v;
    ar[i + 1] = v;
    ar[i + 2] = v;
}
function chekOldBB(x, y) {
    for (var olbb = 1; olbb < 30; olbb++) {
        if (listBB.length - olbb >= 0 && listBB[listBB.length - olbb].inBB(x, y)) return true;
    }
    return false;
}
function picMark(dIm) {
    var w3 = wPic * 3;
    //  var xx = 0;
    for (var i = 2 * w3; i < dIm.length - 3; i += 3) {
        if (mask[i] < 10) {
            setPix(dIm, i, 0);
            continue;
        }
        const cp = pusto[i] + pusto[i + 1] + pusto[i + 2];
        var c1 = dIm[i] + dIm[i + 1] + dIm[i + 2];
        if (Math.abs(c1 - cp) < imgTolerant) {
            setPix(dIm, i, 0);
            c1 = 0;
        }
        if (c1 < 10) {
            if (dIm[i - 9] < 10) {
                setPix(dIm, i - 3, 0); // del .,,.
                setPix(dIm, i - 6, 0); // del .,,.
            } else if (dIm[i - 6] < 10) {
                setPix(dIm, i - 3, 0); // del .,.
            } else if (dIm[i - w3 - w3] < 10) {
                setPix(dIm, i - w3, 0); // del .,.
            }
        }
    }
    // console.log("per 0:", (xx * 3) / (dIm.length - 2 * w3));
    return dIm;
}
async function markBB(dIm, step = 10) {
    listBB = [];

    for (var y = minY + size; y < hPic - size; y += step) {
        var tsize = Math.round(minsize + (maxsize - minsize) * (y / hPic));
        for (var x = 30; x < wPic - step; x += step) {
            if (chekOldBB(x, y)) continue;
            var np = (hPic - y) * wPic + x;

            if (dIm[np * 3] > 0 || dIm[np * 3 - 6] > 0 || dIm[np * 3 + 6] > 0) {
                var co = 0.1;
                var spx = 0;
                var spy = 0;
                for (var iy = -tsize; iy < tsize; iy += 2)
                    for (var ix = -tsize; ix < tsize; ix += 2) {
                        if (dIm[(np + ix + iy * wPic) * 3] > 0) {
                            co++;
                            spx += ix;
                            spy += iy;
                        }
                    }
                const nx = Math.round(
                    Math.min(Math.max(0, x + spx / co - tsize), wPic - 2 * tsize)
                );
                const ny = Math.round(
                    Math.min(Math.max(0, y - spy / co - tsize), hPic - 2 * tsize)
                );
                if (co > 50 && !chekOldBB(nx, ny)) {
                    listBB.push(BB(nx, ny, 2 * tsize, 2 * tsize));
                }
            }
        }
    }
}
async function getImg() {
    var im = [];
    await fetch(jsonInput.dataServer)
        .then((response) => {
            return response.arrayBuffer();
        })
        .then((data) => {
            console.log("loaded", data.byteLength);
            im = data;
        });

    if (im.byteLength < 10000) throw "no load image";
    var numPixels = wPic * hPic;
    var pixels = new Uint8Array(im);
    var ss = 0;
    for (let i = 0; i < numPixels; i++) {
        ss = pixels[i * 3];
        pixels[i * 3] = pixels[i * 3 + 2];
        pixels[i * 3 + 2] = ss;

        mydata.data[i * 4] = pixels[i * 3];
        mydata.data[i * 4 + 1] = pixels[i * 3 + 1];
        mydata.data[i * 4 + 2] = pixels[i * 3 + 2];
    }

    ctx.putImageData(mydata, 0, 0);

    return pixels;
}






//main loop
async function mainLoop(model_name) {
    await loadModel(model_name);
    findMinY();
    console.log("server ready!");
    while (whileLoop) {
        listBB = [];
        shortListBB = [];
        speed.x = ballCoord.x - oldBallCoord.x;
        speed.y = ballCoord.y - oldBallCoord.y;
        oldBallCoord = ballCoord;
        ballCoord = { x: 0, y: 0 };

        //players_list = [];
        bc = 0;
        hc = 0;
        fc = 0;
        if (!pauseState) {
            const image = await getImg();
            const markimg = picMark(image.slice());
            markBB(markimg);
            console.log("mark", listBB.length);
            massDetect(image);
        } else {
            sendData();
        }
        await sleep(2000);
    }
}
function startCheck() {
    console.log("detect", bc, hc, fc);
    claster();
    var dm = 100000;
    for (let i = 0; i < shortListBB.length; i++) {
        const b = shortListBB[i];
        if (b.t == 2 && bc == 1) {
            ballCoord.x = b.xc;
            ballCoord.y = b.yc;
        }
        var d = b.checkDistans(oldBallCoord.x, oldBallCoord.y);
        if (bc == 0 && d < dm && b.t != 0) {
            dm = d;
            ballCoord.x = b.xc;
            ballCoord.y = b.yc;
        }
    }
    if (ballCoord.x == 0) {
        ballCoord.x = oldBallCoord.x + speed.x / 2;
        ballCoord.y = oldBallCoord.y + speed.y / 2;
    }

    if (bc > 0) console.log("ballfound:", ballCoord);
    else console.log("ball NOT found:", ballCoord, bc, hc);

    sendData();
}
async function loadJson() {
    console.log("load:", process.argv[2]);
    jsonInput = await JSON.parse(fs.readFileSync(process.argv[2], (err, data) => data));
    gameId = jsonInput.gameId;
    console.log(jsonInput);
    wPic = jsonInput.width;
    hPic = jsonInput.height;
    minsize = jsonInput.minSize;
    maxsize = jsonInput.maxSize;
    canvFull = canvas.createCanvas(jsonInput.width, jsonInput.height);
    ctx = canvFull.getContext("2d");
    mydata = canvas.createImageData(wPic, hPic);
    for (let pi = 0; pi < wPic * hPic * 4; pi++) {
        mydata.data[pi] = 255;
    }

    mask = readImageFile(jsonInput.mask, true);
    pusto = readImageFile(jsonInput.pusto);

    myserver = http.createServer(server).listen(jsonInput.port, "127.0.0.1", function () {
        console.log(jsonInput);
        console.log("Сервер начал прослушивание запросов на порту " + jsonInput.port);
    });

    mainLoop(jsonInput.baseName);
}
//server
function server(request, response) {
    console.log(request.url);
    response.setHeader("Content-Type", "application/json");
    response.writeHead(200);
    var t = "";

    if (request.url.indexOf("exit") > 0) {
        whileLoop = false;
        response.end("stop Server");
        return;
    }
    if (request.url.indexOf("pusto") > 0) {
        console.log("comand pusto");
        t = "pusto update";
        pusto = readImageFile(jsonInput.pusto);
    }
    if (request.url.indexOf("pause") > 0) {
        console.log("comand pause");
        t = "pause on";
        pauseState = true;
    }
    if (request.url.indexOf("start") > 0) {
        console.log("comand start");
        t = "pause off";
        pauseState = false;
    }

    response.end(t);
}


if (process.argv.length < 3) {
    throw "мало аргументов:  node server.js namegame.json";
}
function sendData() {
    var r = {
        GameID: gameId,
        ballCoord,
        head: [],
        claster: [],
        ballfound: bc == 1,
        pauseState,
        full: [],
    };

    for (let i = 0; i < listClast.length; i++) {
        if (listClast[i].t > 0) {
            r.claster.push({
                x: listClast[i].x,
                y: listClast[i].y,
                w: listClast[i].w,
                h: listClast[i].h,
            });
        }
    }
    for (let i = 0; i < shortListBB.length; i++) {
        if (shortListBB[i].t == 3)
            r.head.push({
                x: shortListBB[i].xc,
                y: shortListBB[i].yc,
            });
        // if (request.url === "/full") {
        //     r.full.push({
        //         ...short_list_bb[i],
        //     });
        // }
    }
    console.log("startSend", jsonInput.zoneAdr, "clast:", r.claster.length);
    fetch(jsonInput.zoneAdr, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(r),
    }).then((response) => response.text());
    // .then((body) => {
    //     console.log("data send", body);

    // });
}

loadJson();

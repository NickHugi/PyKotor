/*
 * @author ndixUR https://github.com/ndixUR
 * tpc.js - write B**Ware TPC files
 *
 * Copyright (C) 2018 ndix UR
 * This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3 or any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/
 *
 * Based on code from the xoreos project, http://xoreos.org
 * Original implementation is for decoding, this implementation is encoding.
 * Compatibility with xoreos code intended for ease of porting.
 */

const fs = require('fs');
const dxt = require('dxt-js');
const cmpntr = require(require('path').normalize(__dirname + '/compressonator.js'));
const EventEmitter = require('events');

//XXX UI STUFF
const $ = require('jquery');

const
    kEncodingNull = 0,
    kEncodingGray = 1,
    kEncodingRGB = 2,
    kEncodingRGBA = 4,
    kEncodingSwizzledBGRA = 12;

const
    kPixelFormatR = 'GL_RED',
    kPixelFormatRGB = 'GL_RGB',
    kPixelFormatRGBA = 'GL_RGBA',
    kPixelFormatBGR = 'GL_BGR',
    kPixelFormatBGRA = 'GL_BGRA';

const
    kPixelFormatR8 = 'GL_R8',
    kPixelFormatRGBA8 = 'GL_RGBA8',
    kPixelFormatRGB8 = 'GL_RGB8',
    kPixelFormatRGB5A1 = 'GL_RGB5_A1',
    kPixelFormatRGB5 = 'GL_RGB5',
    kPixelFormatDXT1 = 'GL_COMPRESSED_RGB_S3TC_DXT1_EXT',
    kPixelFormatDXT3 = 'GL_COMPRESSED_RGBA_S3TC_DXT3_EXT',
    kPixelFormatDXT5 = 'GL_COMPRESSED_RGBA_S3TC_DXT5_EXT';

const
    CMP_PROFILE_VLQ = 'super_fast';
CMP_PROFILE_LQ = 'fast';
CMP_PROFILE_DEFAULT = 'normal';
CMP_PROFILE_HQ = 'slow';
CMP_PROFILE_VHQ = 'ultra';

let image = {
    //dataSize:      0,
    dataSize: 0,
    alphaBlending: 1.0, // MAYBE
    width: 0,
    height: 0,
    encoding: kEncodingRGBA,
    //encoding:      kEncodingRGB,
    mipMapCount: 0,
    format: kPixelFormatBGRA,
    //format:        kPixelFormatBGR,
    formatRaw: kPixelFormatRGBA8,
    //formatRaw:     kPixelFormatDXT1,
    alphaFound: false,
    layerCount: 1,
    layerDim: { width: 0, height: 0 },
    layerPos: [],
    txi: '',
    interpolation: false,
    flip_y: false,
    flip_x: false,
    texture: null,
    compressor: CMP_PROFILE_DEFAULT
};

let feedback = new EventEmitter();

function getDataSize(format, width, height) {
    if (format == kPixelFormatRGB8) {
        return width * height * 3;
    } else if (format == kPixelFormatR8) {
        return width * height;
    } else if (format == kPixelFormatRGBA8) {
        return width * height * 4;
    } else if (format == kPixelFormatRGB5A1 ||
        format == kPixelFormatRGB5) {
        return width * height * 2;
    } else if (format == kPixelFormatDXT1) {
        return Math.max(8, Math.ceil(width / 4) * Math.ceil(height / 4) * 8);
    } else if (format == kPixelFormatDXT3 ||
        format == kPixelFormatDXT5) {
        return Math.max(16, Math.ceil(width / 4) * Math.ceil(height / 4) * 16);
    }
    // this is an error, really
    return 0;
}

function compressionRequested(format) {
    return (
        format == kPixelFormatDXT1 ||
        format == kPixelFormatDXT3 ||
        format == kPixelFormatDXT5
    );
}

// make sure the image structure is returned to a clean (enough) state
function cleanImage() {
    image.texture = null;
    image.txi = '';
    image.width = 0;
    image.height = 0;
    image.size = 0;

    image.layerPos = [];
    image.layerCount = 1;
    image.layerDim = { width: 0, height: 0 };

    image.stat = {};

    image.compressor = CMP_PROFILE_DEFAULT;

    if (image.layers) {
        for (let idx in image.layers) {
            delete image.layers[idx].mipmaps;
            delete image.layers[idx];
        }
    }
}

// given a texture and TXI string, prepare the TPC header & general info
function prepare(texture) {
    // texture is data type from three.js tgaloader
    image.texture = texture;
    image.width = image.texture.image.width;
    image.height = image.texture.image.height;
    image.size = image.width * image.height * 4; // size of ImageData buffer
    //console.log(texture);
    //console.log(texture.pixelDepth);

    // initialize the layer size to entire image size,
    // if multi-layer, this will be adjusted later
    image.layerDim.width = image.texture.image.width;
    image.layerDim.height = image.texture.image.height;

    image.stat = {};

    image.alphaFound = false;
    if (texture.pixelDepth > 24) {
        image.alphaFound = true;
    }

    const use_mode_automatic = (image.encoding == kEncodingNull);
    if (use_mode_automatic) {
        // Resolve automatic compression selection using vanilla compression rules
        if (image.txi &&
            (image.txi.match(/^\s*isbumpmap\s+[1TYty]/im) &&
                image.txi.match(/^\s*compresstexture\s+[0FNfn]/im)) &&
            !image.txi.match(/^\s*proceduretype/im) &&
            texture.pixelDepth >= 24) {
            // normal maps and those with compresstexture 0 set (unless procedural)
            // other vanilla uncompressed textures often mipmap 0 and small size,
            // but we can't make an auto-rule based around that
            settings('compression', 'none');
        } else if (texture.pixelDepth < 24) {
            // 8-bit TGA, assume grayscale bumpmap
            settings('compression', 'grey');
        } else if (texture.pixelDepth > 24) {
            // 32-bit TGA, assume regular alpha-channel texture
            settings('compression', 'dxt5');
        } else {
            // 24-bit TGA, assume regular solid alpha texture
            settings('compression', 'dxt1');
        }
    }

    if (!compressionRequested(image.formatRaw) &&
        texture.pixelDepth == 24) {
        // 24-bit TGA, update pixel format and encoding
        settings('encoding', kEncodingRGB);
        settings('format', kPixelFormatRGB);
        settings('formatRaw', kPixelFormatRGB8);
    } else if (!compressionRequested(image.formatRaw) &&
        texture.pixelDepth == 8) {
        // 8-bit TGA, assume grayscale bumpmap
        settings('compression', 'grey');
    }

    image.mipMapCount = (
        Math.log(Math.max(image.width, image.height)
        ) / Math.log(2)) + 1;
    if (image.encoding == kEncodingGray) {
        image.mipMapCount = 1;
    }

    image.fullImageDataSize = getDataSize(image.formatRaw, image.width, image.height);
    //image.size = image.fullImageDataSize;
    image.dataSize = 0;
    if (compressionRequested(image.formatRaw)) {
        //image.dataSize = getDataSize(image.formatRaw, image.width, image.height);
        image.dataSize = image.fullImageDataSize;
    } else if (image.encoding == kEncodingGray) {
        image.dataSize = image.fullImageDataSize;
    }

    image.layerCount = 1;
    image.layers = [];

    if (image.txi && image.txi.match(/^\s*proceduretype\s+cycle/im)) {
        // animated texture, 1 layer per frame,
        // image.dataSize = layers * layerDataSize (sum w/ all mipmaps)
        console.log('make animated texture');
        let numx, numy;
        numx = image.txi.match(/^\s*numx\s+(\d+)/im);
        numy = image.txi.match(/^\s*numy\s+(\d+)/im);
        defwidth = image.txi.match(/^\s*defaultwidth\s+(\d+)/im);
        defheight = image.txi.match(/^\s*defaultheight\s+(\d+)/im);
        numx = numx ? parseInt(numx[1]) : null;
        numy = numy ? parseInt(numy[1]) : null;
        defwidth = defwidth ? parseInt(defwidth[1]) : null;
        defheight = defheight ? parseInt(defheight[1]) : null;
        if (!defwidth || defwidth > image.width / numx) {
            defwidth = image.width / numx;
        }
        if (!defheight || defheight > image.height / numy) {
            defheight = image.height / numy;
        }
        image.layerCount = numx * numy;
        image.layerDim.width = parseInt(defwidth);
        image.layerDim.height = parseInt(defheight);
        image.layerPos = [];
        for (var y = 0; y < image.height; y += image.layerDim.height) {
            for (var x = 0; x < image.width; x += image.layerDim.width) {
                image.layerPos.push({ x: x, y: y });
            }
        }
        let w = image.layerDim.width;
        let h = image.layerDim.height;
        if (compressionRequested(image.formatRaw)) {
            /*
            if (image.formatRaw != kPixelFormatDXT1) {
              return {error:{
                message: 'DXT1 compression required',
                detail: 'DXT5 animated textures crash the game engine.'
              }};
            }
            */
            image.dataSize = 0;
            while (w >= 1 || h >= 1) {
                image.dataSize += getDataSize(image.formatRaw, w, h);
                w = Math.floor(w / 2);
                h = Math.floor(h / 2);
            }
            //if (image.formatRaw == kPixelFormatDXT1) {
            image.dataSize *= image.layerCount;
            //}
        } else {
            return {
                error: {
                    message: 'compression required',
                    detail: 'Uncompressed animated textures not yet implemented.'
                }
            };
        }
        image.mipMapCount = 1;
    } else if (image.txi && image.txi.match(/^\s*cube\s+1/im)) {
        // cubemap, 6 layers,
        // image.dataSize = layerDataSize (w/o mipmaps)
        console.log('make cubemap texture');
        image.layerCount = 6;
        image.layerDim.width = image.width;
        image.layerDim.height = image.width;
        image.layerPos = [];
        for (var y = 0; y < image.height; y += image.layerDim.width) {
            image.layerPos.push({ x: 0, y: y });
        }
        if (compressionRequested(image.formatRaw)) {
            image.dataSize = getDataSize(image.formatRaw, image.layerDim.width, image.layerDim.width);
        }
        // recompute mipmap count for cubemap based on layer dimension
        image.mipMapCount = (
            Math.log(Math.max(image.layerDim.width, image.layerDim.height)
            ) / Math.log(2)) + 1;
    }

    // test for non-power-of-2 dimension texture
    if ((image.layerDim.width &&
        (image.layerDim.width & (image.layerDim.width - 1))) ||
        (image.layerDim.height &&
            (image.layerDim.height & (image.layerDim.height - 1)))) {
        // try to assert helpful warnings
        // if 24-bit uncompressed, this image will cause issues in K1
        // only power-of-2 dimensions produce clean mipmaps
    }

    // move pixel data from texture buffer to layers structure
    if (image.layerPos && image.layerPos.length) {
        for (let pos of image.layerPos) {
            image.layers.push({
                mipmaps: [
                    getImageData(
                        image.texture.mipmaps[0], image.width, pos.x, pos.y,
                        image.layerDim.width, image.layerDim.height
                    )
                ],
                width: image.layerDim.width,
                height: image.layerDim.height,
            });
        }
    } else {
        image.layers.push({
            mipmaps: [
                image.texture.mipmaps[0]
            ],
            width: image.width,
            height: image.height,
        });
    }
    // generate pixel data for lower detail level mipmaps
    generateDetailLevels(image.layers);

    // save output format to status
    image.stat = image.stat || {};
    switch (image.formatRaw) {
        case kPixelFormatDXT1:
            image.stat.format = 'DXT1';
            break;
        case kPixelFormatDXT5:
            image.stat.format = 'DXT5';
            break;
        case kPixelFormatRGBA8:
        case kPixelFormatRGB8:
        case kPixelFormatR8:
            image.stat.format = 'Raw';
            /*
            image.stat.format = '32bpp';
            image.stat.format = '24bpp';
            image.stat.format = '8bpp';
            */
            break;
    }

    // if using a compressonator profile, initialize worker pool now
    if (image.compressor != CMP_PROFILE_VLQ) {
        cmpntr.pool_init();
    }

    // n power of 2? n && (n & (n - 1)) === 0;
    //console.log(image);
    return image;
};

// emit overall progress of current TPC file encoding process
function progress(nprog, op, layer) {
    // begin by interpreting nprog as global progress of overall encoding process
    let cur_prog = nprog;
    const phase_map = {
        'scale': 0.3,
        'compress': 0.7
    };
    const phase_order = [
        'scale', 'compress'
    ];
    if (nprog == null &&
        (!op || !phase_map[op])) {
        return;
    }
    // a phase is specified, so now interpret nprog as progess in-phase
    if (op && phase_map[op]) {
        // operator gives us its own progress,
        // fit it into global status here
        const layer_factor = 1 / image.layerCount;
        cur_prog = 0.0;
        let op_scale = 0.0;
        // accumulate progress of finished phases
        for (let pk of phase_order) {
            if (pk != op) {
                cur_prog += phase_map[pk];
            } else {
                break;
            }
        }
        cur_prog = cur_prog +
            // finished layers
            ((layer - 1) * phase_map[op] * layer_factor) +
            // current layer
            (nprog * phase_map[op] * layer_factor);
    }
    feedback.emit('progress', cur_prog);
}

async function generateDetailLevel(layer, layer_idx, mip_idx) {
    const pixels = layer.mipmaps[mip_idx - 1];
    const width = Math.floor(Math.max(layer.width / Math.pow(2, mip_idx), 1));
    const height = Math.floor(Math.max(layer.height / Math.pow(2, mip_idx), 1));
    const parent_width = Math.floor(Math.max(
        layer.width / Math.pow(2, mip_idx - 1), 1
    ));
    const parent_height = Math.floor(Math.max(
        layer.height / Math.pow(2, mip_idx - 1), 1
    ));
    const progress_range = [
        1 - (Math.pow(0.5, (Math.log(Math.pow(2, mip_idx) / 2) / Math.log(2)) + 1)),
        1 - (Math.pow(0.5, (Math.log(Math.pow(2, mip_idx)) / Math.log(2)) + 1))
    ];
    const bytes_per_pixel = 4;
    layer.mipmaps.push(new Uint8ClampedArray(width * height * bytes_per_pixel));
    // we need to do a weighted average if downsizing from a parent with
    // non-even dimensions because a simple 4x4 sample won't be accurate
    const use_full_interp = (parent_width % 2 || parent_height % 2);
    for (let y_iter = 0; y_iter < height; y_iter++) {
        const y_scaled = Math.floor(y_iter * (parent_height / height));
        // pymin, pymax is the Y range of parent pixels to sample
        const pymin = (y_iter / height) * parent_height;
        const pymax = ((y_iter + 1) / height) * parent_height;
        for (let x_iter = 0; x_iter < width; x_iter++) {
            const x_scaled = Math.floor(x_iter * (parent_width / width));
            const in_index = ((y_scaled * parent_width) + x_scaled) * bytes_per_pixel;
            const out_index = ((y_iter * width) + x_iter) * bytes_per_pixel;
            // pxmin, pxmax is the X range of parent pixels to sample
            const pxmin = (x_iter / width) * parent_width;
            const pxmax = ((x_iter + 1) / width) * parent_width;
            const weights = { total: 0.0 };
            if (use_full_interp) {
                // generate weights for averaging parent detail level pixels
                // contributing to this pixel
                for (let py = Math.floor(pymin); py <= Math.floor(pymax); py++) {
                    for (let px = Math.floor(pxmin); px <= Math.floor(pxmax); px++) {
                        const key = px + ',' + py;
                        weights[key] = 1.0
                        if (px < pxmin) weights[key] *= (px + 1) - pxmin;
                        if (py < pymin) weights[key] *= (py + 1) - pymin;
                        if (px == Math.floor(pxmax) && pxmax >= px) weights[key] *= pxmax - px;
                        if (py == Math.floor(pymax) && pymax >= py) weights[key] *= pymax - py;
                        weights.total += weights[key];
                    }
                }
            }
            for (let i = 0; i < bytes_per_pixel; i++) {
                let datum;
                if (!use_full_interp && !image.interpolation) {
                    // basic case, bilinear interpolation,
                    // (average of 2x2 grid from next mipmap up)
                    datum = Math.round((
                        pixels[in_index + i] +
                        pixels[(in_index + bytes_per_pixel) + i] +
                        pixels[(in_index + (parent_width * bytes_per_pixel)) + i] +
                        pixels[(in_index + bytes_per_pixel + (parent_width * bytes_per_pixel)) + i]
                    ) * 0.25);
                } else if (use_full_interp) {
                    // intermediate case, bilinear interpolation for unclean downsize
                    // (weighted average of 2-2.5x2-2.5 grid from next mipmap up)
                    datum = 0;
                    datum_grid = weights.total;
                    for (let py = Math.floor(pymin); py <= Math.min(Math.floor(pymax), parent_height - 1); py++) {
                        for (let px = Math.floor(pxmin); px <= Math.min(Math.floor(pxmax), parent_width - 1); px++) {
                            if (weights[px + ',' + py] > 0.0) {
                                // not using datum += here for chromium optimizer purpose
                                datum = datum + (
                                    pixels[(((py * parent_width) + px) * bytes_per_pixel) + i] *
                                    weights[px + ',' + py]
                                );
                            }
                        }
                    }
                    datum = Math.round(datum / weights.total);
                } else if (!use_full_interp && image.interpolation) {
                    // advanced case, bicubic interpolation,
                    // (complex derivation of 4x4 grid from next mipmap up)

                    // determine pixel offsets for use in bicubic interpolation
                    // in_index has pixel (red channel) under consideration
                    // so, in_index + i = datum under consideration,
                    // '-2,-2' = (in_index + i) + (-2 * 4 * int_scaler) + (-2 * 4 * int_scaler * image.width)

                    // determine grid points to use,
                    // asymmetrical because our x,y iterators step through parent,
                    // like 0, 2, ... n -1, if they were 1, 3, ... n,
                    // we would see the reverse symmetry
                    const x_pts = [-1, 0, 1, 2];
                    const y_pts = [-1, 0, 1, 2];
                    // for first & last, repeat a pixel because only 1 is available
                    if (x_iter == 0) {
                        x_pts[0] = 0;
                    } else if (x_iter == width - 1) {
                        x_pts[3] = 1;
                    }
                    if (y_iter == 0) {
                        y_pts[0] = 0;
                    } else if (y_iter == height - 1) {
                        y_pts[3] = 1;
                    }

                    // this is an unrolled 4x4 dual nested loop, foul business,
                    // but yields 3.5x performance improvement
                    let p = [
                        [
                            // 0, 0
                            pixels[
                            (in_index + i) +
                            (x_pts[0] * 4) +
                            (y_pts[0] * 4 * parent_width)
                            ],
                            // 0, 1
                            pixels[
                            (in_index + i) +
                            (x_pts[0] * 4) +
                            (y_pts[1] * 4 * parent_width)
                            ],
                            // 0, 2
                            pixels[
                            (in_index + i) +
                            (x_pts[0] * 4) +
                            (y_pts[2] * 4 * parent_width)
                            ],
                            // 0, 3
                            pixels[
                            (in_index + i) +
                            (x_pts[0] * 4) +
                            (y_pts[3] * 4 * parent_width)
                            ],
                        ],
                        [
                            // 1, 0
                            pixels[
                            (in_index + i) +
                            (x_pts[1] * 4) +
                            (y_pts[0] * 4 * parent_width)
                            ],
                            // 1, 1
                            pixels[
                            (in_index + i) +
                            (x_pts[1] * 4) +
                            (y_pts[1] * 4 * parent_width)
                            ],
                            // 1, 2
                            pixels[
                            (in_index + i) +
                            (x_pts[1] * 4) +
                            (y_pts[2] * 4 * parent_width)
                            ],
                            // 1, 3
                            pixels[
                            (in_index + i) +
                            (x_pts[1] * 4) +
                            (y_pts[3] * 4 * parent_width)
                            ],
                        ],
                        [
                            // 2, 0
                            pixels[
                            (in_index + i) +
                            (x_pts[2] * 4) +
                            (y_pts[0] * 4 * parent_width)
                            ],
                            // 2, 1
                            pixels[
                            (in_index + i) +
                            (x_pts[2] * 4) +
                            (y_pts[1] * 4 * parent_width)
                            ],
                            // 2, 2
                            pixels[
                            (in_index + i) +
                            (x_pts[2] * 4) +
                            (y_pts[2] * 4 * parent_width)
                            ],
                            // 2, 3
                            pixels[
                            (in_index + i) +
                            (x_pts[2] * 4) +
                            (y_pts[3] * 4 * parent_width)
                            ],
                        ],
                        [
                            // 3, 0
                            pixels[
                            (in_index + i) +
                            (x_pts[3] * 4) +
                            (y_pts[0] * 4 * parent_width)
                            ],
                            // 3, 1
                            pixels[
                            (in_index + i) +
                            (x_pts[3] * 4) +
                            (y_pts[1] * 4 * parent_width)
                            ],
                            // 3, 2
                            pixels[
                            (in_index + i) +
                            (x_pts[3] * 4) +
                            (y_pts[2] * 4 * parent_width)
                            ],
                            // 3, 3
                            pixels[
                            (in_index + i) +
                            (x_pts[3] * 4) +
                            (y_pts[3] * 4 * parent_width)
                            ],
                        ]
                    ];
                    /*
                    let p = [ [], [], [], [] ];
                    for (let col in x_pts) {
                      let xpt = x_pts[col];
                      for (let row in y_pts) {
                        let ypt = y_pts[row];
                        / *
                        console.log(
                          x_scaled, y_scaled, xpt, ypt,
                          int_scaler, i, in_index, '=>',
                          (in_index + i) + (xpt * 4 * int_scaler) + (ypt * 4 * int_scaler * image.width)
                        );
                        * /
                        p[col][row] = pixels[
                          (in_index + i) +
                          (xpt * 4 * int_scaler) +
                          (ypt * 4 * int_scaler * layer_width)
                        ];
                      }
                    }
                    */
                    // constrain result to 0-255 range
                    datum = Math.round(
                        Math.max(0, Math.min(255,
                            bicubic_interpolation(p, 0.5, 0.5)
                        ))
                    );
                }
                layer.mipmaps[mip_idx][out_index + i] = datum;
            }
        }
    }
    /*
    // this code adds canvases for every mipmap to head of html document
    let mmapcv = $(`<canvas class="orig" width="${width}" height="${height}"></canvas>`).get(0);
    const octx = mmapcv.getContext('2d');
    const id = octx.createImageData(width, height);
    id.data.set(layer.mipmaps[mip_idx]);
    octx.putImageData(id,0,0);
    $('body').prepend(mmapcv);
    */
    progress(progress_range[1], 'scale', layer_idx + 1);
}

// create mipmap pixel data for all layers
async function generateDetailLevels(layers) {
    layers = layers || [];
    const bytes_per_pixel = 4;
    for (let layer_idx in layers) {
        const layer = layers[layer_idx];
        const num_detail_levels = (
            Math.log(Math.max(layer.width, layer.height)) / Math.log(2)
        ) + 1;
        for (let mip_idx = 1; mip_idx < num_detail_levels; mip_idx++) {
            await generateDetailLevel(layer, parseInt(layer_idx), mip_idx);
        }
    }
}

/*
 * Asynchronous write flow:
 * write_data, write_mipmap (reentrant), write_txi, callback
 */
function write_data(stream, image, cb) {
    let width = image.width,
        height = image.height,
        size = image.size,
        scale = 1,
        layer = 1,
        filepos = 128;
    if (image.layerCount > 1) {
        width = image.layerDim.width;
        height = image.layerDim.height;
        size = width * height * 4;
    }
    //XXX UI STUFF
    //let cbound = [ $('.preview').get(0).offsetWidth, $('.preview').get(0).offsetWidth ];
    //console.log($('.preview').get(0));
    let visual_scale = Math.min(1, $('.preview').get(0).offsetWidth / width);
    let cbound = [width * visual_scale, height * visual_scale * 2];
    //let cbound = [ Math.min(image.width, $('.preview').get(0).offsetWidth), $('.preview').get(0).offsetWidth * 2 ];
    $('.preview').prepend(`<canvas width="${cbound[0]}" height="${cbound[1]}"></canvas>`);
    //$('.preview').prepend(`<canvas width="${image.width}" height="${image.height}"></canvas>`);
    /*
    let ctx = $('.preview > canvas').get(0).getContext('2d');
    ctx.scale($('.preview').get(0).offsetWidth / image.width,
              $('.preview').get(0).offsetWidth / image.width);
    */
    //console.log($('.preview').get(0).offsetWidth / image.width);
    write_mipmap(stream, image, width, height, size, scale, filepos, layer, cb);
}

// emulate the canvas 2d drawing context getImageData function,
// providing a linearized data buffer containing an arbitrary rectangle
function getImageData(data, width, x, y, w, h) {
    // short circuit this special case to prevent needless copy
    if (w * h * 4 == data.byteLength) {
        return data;
    }
    const imageData = new Uint8ClampedArray(w * h * 4);
    //console.log(imageData.byteLength);
    //console.log(`width ${width} x ${x} y ${y} w ${w} h ${h}`);
    let imgData_offset = 0;
    for (let i = y; i < y + h; i++) {
        const row_begin = (x + (i * width)) * 4;
        const row_end = row_begin + (w * 4);
        imageData.set(data.subarray(row_begin, row_end), imgData_offset);
        imgData_offset = imgData_offset + (row_end - row_begin);
    }
    return imageData;
}

async function write_mipmap(stream, image, width, height, size, scale, filepos, layer, cb) {
    if (width < 1 && height < 1) { // || (image.width / width) > image.mipMapCount) {
        // we write mipmaps until we reach 1 pixel in both dimensions
        // the next/final step is writing the txi data
        if (layer < image.layerCount) {
            // reenter write_mipmap here if more layers must be written
            return write_mipmap(
                stream, image,
                image.layerDim.width, image.layerDim.height,
                image.layerDim.width * image.layerDim.height * 4,
                1, filepos, layer + 1,
                cb
            );
        }
        return write_txi(stream, image, cb);
    }
    width = Math.floor(Math.max(width, 1));
    height = Math.floor(Math.max(height, 1));

    //XXX UI STUFF
    // create off-screen canvas in size of this mipmap, will be input for preview
    let mmapcv = $(`<canvas width="${width}" height="${height}"></canvas>`).get(0);
    let octx = mmapcv.getContext('2d');
    let img = octx.createImageData(width, height);

    let compressed_size = getDataSize(image.formatRaw, width, height);

    const mipmap_index = (Math.log(scale) / Math.log(2));

    console.log(
        'layer ' + layer + ' mipmap ' + (Math.log(scale) / Math.log(2)) + ': ' +
        filepos + '-' + (filepos + compressed_size) + ' (' + compressed_size + ') ' +
        '(' + width + ',' + height + ')'
    );

    // compute layer-relative progress at beginning and end of this mipmap
    const progress_range = [
        1 - (Math.pow(0.5, (Math.log(scale / 2) / Math.log(2)) + 1)),
        1 - (Math.pow(0.5, (Math.log(scale) / Math.log(2)) + 1))
    ];

    // grab the appropriate pre-formatted pixel buffer
    let mipmap = image.layers[layer - 1].mipmaps[mipmap_index];

    // process visual flip horizontal/vertical now so it shows in the preview
    // use buffers and double swaps to avoid iterating over every pixel
    if (image.flip_y || image.flip_x) {
        const row_buffer = new Uint8ClampedArray(width * 4);
        for (let src_y = 0; src_y < height / 2; src_y++) {
            const tgt_y = (height - 1) - src_y;
            const tgt_offset = tgt_y * row_buffer.byteLength;
            const src_offset = src_y * row_buffer.byteLength;
            if (image.flip_x) {
                const pixel_buffer = new Uint8ClampedArray(4);
                for (let src_x = 0; src_x < width / 2; src_x++) {
                    const tgt_x = (width - 1) - src_x;
                    if (src_x == tgt_x) {
                        break;
                    }
                    const tgt1_xoffset = src_offset + (tgt_x * 4);
                    const src1_xoffset = src_offset + (src_x * 4);
                    const tgt2_xoffset = tgt_offset + (tgt_x * 4);
                    const src2_xoffset = tgt_offset + (src_x * 4);
                    // write target pixel to buffer
                    pixel_buffer.set(mipmap.subarray(tgt1_xoffset, tgt1_xoffset + 4));
                    // write source pixel to target location
                    mipmap.set(mipmap.subarray(src1_xoffset, src1_xoffset + 4), tgt1_xoffset);
                    // write buffer to source location
                    mipmap.set(pixel_buffer, src1_xoffset);
                    // write target pixel to buffer
                    pixel_buffer.set(mipmap.subarray(tgt2_xoffset, tgt2_xoffset + 4));
                    // write source pixel to target location
                    mipmap.set(mipmap.subarray(src2_xoffset, src2_xoffset + 4), tgt2_xoffset);
                    // write buffer to source location
                    mipmap.set(pixel_buffer, src2_xoffset);
                }
            }
            if (image.flip_y && src_y < tgt_y) {
                // write target row to buffer
                row_buffer.set(mipmap.subarray(tgt_offset, tgt_offset + row_buffer.byteLength));
                // write source row to target location
                mipmap.set(mipmap.subarray(src_offset, src_offset + row_buffer.byteLength), tgt_offset);
                // write buffer to source location
                mipmap.set(row_buffer, src_offset);
            }
        }
    }

    // draw the mipmap buffer to full-size offscreen canvas
    img.data.set(mipmap);
    octx.putImageData(img, 0, 0);

    // draw the off-screen canvas image to preview canvas,
    // appropriately scaled and positioned
    let draw_ctx = $('.preview canvas').get(0).getContext('2d');
    draw_ctx.imageSmoothingEnabled = false;
    const visual_scale = Math.min(1, $('.preview canvas').get(0).offsetWidth / image.layers[0].width);
    draw_ctx.drawImage(
        mmapcv,
        0, 0, width, height,
        0, (2 * image.layers[layer - 1].height * visual_scale) - (2 * height * visual_scale),
        width * visual_scale, height * visual_scale
        //0, ((2 * image.height) - (2 * height)),
        //0, ((2 * layer_height) - (2 * height)) * Math.min(1, $('.preview canvas').get(0).offsetWidth / layer_height),
        //0, ((2 * image.layers[layer - 1].height) - (2 * height)) * Math.min(1, $('.preview canvas').get(0).offsetWidth / image.layers[0].height),
        //Math.min(width, $('.preview canvas').get(0).offsetWidth / scale),
        //Math.min(height, $('.preview canvas').get(0).offsetWidth / scale)
    );

    // at this point, all mipmap buffers are in html canvas coordinate system,
    // which is origin in upper left, game wants opengl-convention bottom left,
    // so we do another row swap here using row buffer to avoid full image copy
    const row_buffer = new Uint8ClampedArray(width * 4);
    for (let src_y = 0; src_y < height / 2; src_y++) {
        const tgt_y = (height - 1) - src_y;
        if (src_y == tgt_y) {
            break;
        }
        const tgt_offset = tgt_y * row_buffer.byteLength;
        const src_offset = src_y * row_buffer.byteLength;
        // write target row to buffer
        row_buffer.set(mipmap.subarray(tgt_offset, tgt_offset + row_buffer.byteLength));
        // write source row to target location
        mipmap.set(mipmap.subarray(src_offset, src_offset + row_buffer.byteLength), tgt_offset);
        // write buffer to source location
        mipmap.set(row_buffer, src_offset);
    }

    // at this point, all mipmap buffers are RGBA,
    // if the user is requesting a 24-bit uncompressed format,
    // strip alpha bytes now (DXT1 compression expects RGBA input buffer)
    if (!image.alphaFound && !compressionRequested(image.formatRaw)) {
        let pixel_bytes = 3;
        if (image.encoding == kEncodingGray) {
            pixel_bytes = 1;
        }
        const temp2 = new Uint8ClampedArray((mipmap.byteLength / 4) * pixel_bytes);
        var temp_offset = 0;
        for (let y = 0; y < height; y++) {
            const row_begin = (y * width) * 4;
            //console.log(`${row_begin} @${temp_offset}`);
            for (let x = 0; x < width; x++) {
                // start position is based on 4-byte offset
                const pixel_begin = row_begin + (x * 4);
                // only copy `pixel_bytes` number of bytes
                temp2.set(mipmap.subarray(pixel_begin, pixel_begin + pixel_bytes), temp_offset);
                temp_offset += pixel_bytes;
            }
        }
        //console.log(`size change: ${mipmap.byteLength} ${temp2.byteLength}`);
        mipmap = temp2;
    }

    let img_buf;
    if (compressionRequested(image.formatRaw)) {
        const cmp_opts = {};
        let compression_flags = dxt.flags.ColourIterativeClusterFit |
            dxt.flags.ColourMetricPerceptual;
        if (image.formatRaw == kPixelFormatDXT1) {
            compression_flags |= dxt.flags.DXT1;
            cmp_opts.encoding = cmpntr.ENCODING_DXT1;
        } else if (image.formatRaw == kPixelFormatDXT3) {
            compression_flags |= dxt.flags.DXT3;
        } else if (image.formatRaw == kPixelFormatDXT5) {
            compression_flags |= dxt.flags.DXT5;
            cmp_opts.encoding = cmpntr.ENCODING_DXT5;
        }
        //let compress = dxt.compress(mipmap.buffer, width, height, compression_flags);
        //console.log(Buffer.from(mipmap.buffer));

        // default settings for compressonator DXT compression engine
        cmp_opts.UseChannelWeighting = true;
        cmp_opts.UseAdaptiveWeighting = true;
        cmp_opts.CompressionSpeed = cmpntr.CMP_Speed_Normal;
        cmp_opts['3DRefinement'] = false;
        cmp_opts.RefinementSteps = 1;
        // provide a progress feedback function to the compressor
        cmp_opts.progress = (p) => {
            progress(
                (p * (progress_range[1] - progress_range[0])) + progress_range[0],
                'compress', layer
            );
        }
        // profile-based settings for compressonator
        // note: VLQ profile uses old libsquish compressor
        switch (image.compressor) {
            case CMP_PROFILE_LQ:
                cmp_opts.CompressionSpeed = cmpntr.CMP_Speed_Fast;
                break;
            case CMP_PROFILE_DEFAULT:
                cmp_opts.RefinementSteps = 2;
                break;
            case CMP_PROFILE_HQ:
                cmp_opts.RefinementSteps = 6;
                break;
            case CMP_PROFILE_VHQ:
                cmp_opts['3DRefinement'] = true;
                cmp_opts.RefinementSteps = 2;
                break;
        }

        let compress;
        try {
            if (image.compressor == CMP_PROFILE_VLQ) {
                compress = dxt.compress(Buffer.from(mipmap.buffer), width, height, compression_flags);
            } else {
                compress = await cmpntr.compress(mipmap, width, height, cmp_opts);
            }
        } catch (err) {
            console.log(err);
            return cb({ message: 'compression failed', detail: 'DXT compress failed.' });
        }
        //console.log(compress);
        img_buf = Buffer.from(compress);
        //img_buf = compress;
        //console.log(img_buf);
    } else {
        img_buf = Buffer.from(mipmap.buffer);
    }

    // write the mipmap to the TPC output file
    //stream.write(Buffer.from(mipmap.buffer), function(err, bytesWritten, buffer) {
    stream.write(img_buf, function (err, bytesWritten, buffer) {
        if (err) { console.log(err); return; }
        //(Math.log(scale) / Math.log(2)) == mipmap # 
        // mipmap progress = 50% * mipmap num * 50%
        progress(progress_range[1], 'compress', layer);
        // prepare settings for next run
        //filepos += size;
        //console.log(bytesWritten);
        //filepos += size;
        filepos += compressed_size;
        scale *= 2;
        width /= 2;
        height /= 2;
        width = Math.floor(width);
        height = Math.floor(height);
        size = width * height * 4;
        //XXX Hack to short-circuit detail level generation for grayscale images
        if (image.encoding == kEncodingGray) {
            width = 0;
            height = 0;
        }
        //console.log(scale, width, height, size, filepos);
        // proceed to next mipmap, allow UI update w/ immediate timeout
        setTimeout(function () {
            write_mipmap(stream, image, width, height, size, scale, filepos, layer, cb);
        }, 0);
    });
}

function write_txi(stream, image, cb) {
    let image_status = null;
    if (image && image.stat) {
        image_status = image.stat;
    }
    if (!image || !image.txi || !image.txi.length) {
        progress(1.0);
        stream.end();
        cleanImage();
        cmpntr.pool_cleanup();
        if (cb) return cb(null, image_status);
        return;
    }
    image_status.txi = true;
    // vanilla tpc uses windows line endings, so replicate that
    image.txi = image.txi.trim().replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
    // add trailing carriage return/newline
    image.txi += '\r\n';
    stream.write(image.txi, function (err, bytesWritten, buffer) {
        if (err) { console.log(err); return; }
        progress(1.0);
        // final success, callback
        stream.end();
        cleanImage();
        cmpntr.pool_cleanup();
        if (cb) return cb(null, image_status);
        return;
    });
}

/**********************
 * export TPC file for texture, with txi text, interpolate if requested
 * cb called upon completion
 * @public
 */
function export_tpc(filename, texture, cb) {
    /*
    if (fs.existsSync(filename)) {
      console.log(filename + ' already exists');
      return null;
    }
    */
    //txi = txi || '';
    //interpolation = interpolation || false;
    //console.log(image);
    //console.log(texture);
    progress(0);

    let result = prepare(texture);

    if (!result) {
        return cb({
            message: 'unknown failure',
            detail: 'Unable to prepare texture for unknown reason.'
        });
    }
    if (result.error) {
        return cb(result.error);
    }
    progress(0.01);

    //image.txi             = txi;
    //image.interpolation   = interpolation;
    //console.log(image);

    // construct the header as a Uint8 byte array
    let header = new Uint8Array(128);
    let dv = new DataView(header.buffer);
    dv.setUint32(0, image.dataSize, true);
    dv.setFloat32(4, image.alphaBlending, true);
    dv.setUint16(8, image.width, true);
    dv.setUint16(10, image.height, true);
    header[12] = image.encoding;
    header[13] = image.mipMapCount;
    for (let i = 0; i < 114; i++) {
        header[14 + i] = 0;
    }
    //console.log(header);

    // open a write stream for the TPC output file
    let tpc_stream = fs.createWriteStream(filename, {
        autoClose: true
    });
    // when open, write the header
    tpc_stream.addListener('open', function (fd) {
        tpc_stream.write(Buffer.from(header.buffer), function (err, bytesWritten, buffer) {
            //console.log(err);
            //console.log('wrote header to ' + filename);
            // header is written, proceed to writing data
            write_data(tpc_stream, image, cb);
        });
    });
    tpc_stream.addListener('error', function (err) {
        //console.log(err);
        return cb({
            message: 'unknown failure',
            detail: 'Unable to write file for unknown reason.'
        });
    });
}

/**********************
 * cubic interpolation methods, used for bicubic interpolation on reduced size mipmaps
 */
// basic cubic interpolation
function cubic_interpolation(p, x) {
    return p[1] + 0.5 * x * (
        p[2] - p[0] + x * (
            2.0 * p[0] - 5.0 * p[1] + 4.0 * p[2] - p[3] + x * (
                3.0 * (p[1] - p[2]) + p[3] - p[0]
            )
        )
    );
}

// bicubic interpolation built on basic cubic interpolator
function bicubic_interpolation(p, x, y) {
    let result = [
        cubic_interpolation(p[0], y),
        cubic_interpolation(p[1], y),
        cubic_interpolation(p[2], y),
        cubic_interpolation(p[3], y),
    ];
    return cubic_interpolation(result, x);
}

/*
 *
 */
function settings(key, value) {
    if (!key) {
        return image;
    }
    if (key == 'compression') {
        // this is a special composite setting with possible values:
        // auto, none, dxt1, dxt3, dxt5
        if (value == 'none') {
            image.dataSize = 0;
            image.encoding = kEncodingRGBA;
            image.format = kPixelFormatRGBA;
            image.formatRaw = kPixelFormatRGBA8;
        } else if (value == 'auto') {
            image.encoding = kEncodingNull;
        } else if (value == 'grey') {
            image.encoding = kEncodingGray;
            image.format = kPixelFormatR;
            image.formatRaw = kPixelFormatR8;
        } else if (value == 'dxt1') {
            image.encoding = kEncodingRGB;
            image.format = kPixelFormatBGR;
            image.formatRaw = kPixelFormatDXT1;
        } else if (value == 'dxt3') {
            image.encoding = kEncodingRGBA;
            image.format = kPixelFormatBGRA;
            image.formatRaw = kPixelFormatDXT3;
        } else if (value == 'dxt5') {
            image.encoding = kEncodingRGBA;
            image.format = kPixelFormatBGRA;
            image.formatRaw = kPixelFormatDXT5;
        }
        return;
    }
    image[key] = value;
}

// MODULE EXPORTS
module.exports = {
    export_tpc: export_tpc,
    settings: settings,
    feedback: feedback,
};
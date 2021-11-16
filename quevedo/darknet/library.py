"""
Python 3 wrapper for identifying objects in images

Requires DLL compilation

On a GPU system, you can force CPU evaluation by any of:

- Set global variable DARKNET_FORCE_CPU to True
- Set environment variable CUDA_VISIBLE_DEVICES to -1
- Set environment variable "FORCE_CPU" to "true"

Original *nix 2.7: https://github.com/pjreddie/darknet/blob/0f110834f4e18b30d5f101bf8f1724c34b7b83db/python/darknet.py
Windows Python 2.7 version: https://github.com/AlexeyAB/darknet/blob/fc496d52bf22a0bb257300d3c79be9cd80e722cb/build/darknet/x64/darknet.py
Created Philip Kahn 2018-05-03

Modified Antonio F. G. Sevilla <afgs@ucm.es> 2020-07-09, 2021-04-21
"""

from ctypes import *
import os
import PIL
import sys


def supress_stdio():
    fdo = sys.stdout.fileno()
    fde = sys.stderr.fileno()
    old_stdout = os.fdopen(os.dup(fdo), 'w')
    old_stderr = os.fdopen(os.dup(fde), 'w')
    with open(os.devnull, 'w') as file:
        sys.stdout.close()  # + implicit flush()
        sys.stderr.close()  # + implicit flush()
        os.dup2(file.fileno(), fdo)  # fdo writes to 'to' file
        os.dup2(file.fileno(), fde)  # fde writes to 'to' file
        sys.stdout = os.fdopen(fdo, 'w')  # Python writes to fdo
        sys.stderr = os.fdopen(fde, 'w')  # Python writes to fde
    return [fdo, fde, old_stdout, old_stderr]


def restore_stdio(supressed):
    fdo, fde, old_stdout, old_stderr = supressed
    sys.stdout.close()  # + implicit flush()
    sys.stderr.close()  # + implicit flush()
    os.dup2(old_stdout.fileno(), fdo)  # fdo writes to 'to' file
    os.dup2(old_stderr.fileno(), fde)  # fde writes to 'to' file
    sys.stdout = os.fdopen(fdo, 'w')  # Python writes to fdo
    sys.stderr = os.fdopen(fde, 'w')  # Python writes to fde


def cstr(s):
    return str(s).encode('utf8')


def c_array(ctype, values):
    arr = (ctype*len(values))()
    arr[:] = values
    return arr


class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]


class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int),
                ("uc", POINTER(c_float)),
                ("points", c_int),
                ("embeddings", POINTER(c_float)),
                ("embedding_size", c_int),
                ("sim", c_float),
                ("track_id", c_int)]


class DETNUMPAIR(Structure):
    _fields_ = [("num", c_int),
                ("dets", POINTER(DETECTION))]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]


class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]


class DarknetNetwork():

    def __init__ (self, libraryPath=None, configPath=None, weightPath=None,
                  metaPath=None, shutupDarknet=True):

        self.netMain = None
        self.metaMain = None
        self.altNames = None

        # If shutupDarknet is False, no stdout/stderr magic is used, so Darknet
        # will spew A LOT of text on them. Consider define-ing printf and
        # fprintf to empty and recompiling darknet
        self.shutupDarknet = shutupDarknet
        if shutupDarknet: suppressed = supress_stdio()

        libraryPath = cstr(libraryPath)
        configPath = cstr(configPath)
        weightPath = cstr(weightPath)
        metaPath = cstr(metaPath)

        hasGPU = True
        if os.name == "nt":
            cwd = os.path.dirname(__file__)
            os.environ['PATH'] = cwd + ';' + os.environ['PATH']
            winGPUdll = os.path.join(cwd, "yolo_cpp_dll.dll")
            winNoGPUdll = os.path.join(cwd, "yolo_cpp_dll_nogpu.dll")
            envKeys = list()
            for k, v in os.environ.items():
                envKeys.append(k)
            try:
                try:
                    tmp = os.environ["FORCE_CPU"].lower()
                    if tmp in ["1", "true", "yes", "on"]:
                        raise ValueError("ForceCPU")
                    else:
                        print("Flag value '"+tmp+"' not forcing CPU mode")
                except KeyError:
                    # We never set the flag
                    if 'CUDA_VISIBLE_DEVICES' in envKeys:
                        if int(os.environ['CUDA_VISIBLE_DEVICES']) < 0:
                            raise ValueError("ForceCPU")
                    try:
                        global DARKNET_FORCE_CPU
                        if DARKNET_FORCE_CPU:
                            raise ValueError("ForceCPU")
                    except NameError:
                        pass
                    # print(os.environ.keys())
                    # print("FORCE_CPU flag undefined, proceeding with GPU")
                if not os.path.exists(winGPUdll):
                    raise ValueError("NoDLL")
                lib = CDLL(winGPUdll, RTLD_GLOBAL)
            except (KeyError, ValueError):
                hasGPU = False
                if os.path.exists(winNoGPUdll):
                    lib = CDLL(winNoGPUdll, RTLD_GLOBAL)
                    print("Notice: CPU-only mode")
                else:
                    # Try the other way, in case no_gpu was
                    # compile but not renamed
                    lib = CDLL(winGPUdll, RTLD_GLOBAL)
                    print("Environment variables indicated a CPU run, but we didn't find `"+winNoGPUdll+"`. Trying a GPU run anyway.")
        else:
            lib = CDLL(libraryPath, RTLD_GLOBAL)

        if shutupDarknet: restore_stdio(suppressed)

        lib.network_width.argtypes = [c_void_p]
        lib.network_width.restype = c_int
        lib.network_height.argtypes = [c_void_p]
        lib.network_height.restype = c_int

        copy_image_from_bytes = lib.copy_image_from_bytes
        copy_image_from_bytes.argtypes = [IMAGE,c_char_p]

        def network_width(net):
            return lib.network_width(net)

        def network_height(net):
            return lib.network_height(net)

        predict = lib.network_predict_ptr
        predict.argtypes = [c_void_p, POINTER(c_float)]
        predict.restype = POINTER(c_float)

        if hasGPU:
            set_gpu = lib.cuda_set_device
            set_gpu.argtypes = [c_int]

        init_cpu = lib.init_cpu

        make_image = lib.make_image
        make_image.argtypes = [c_int, c_int, c_int]
        make_image.restype = IMAGE

        get_network_boxes = lib.get_network_boxes
        get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int), c_int]
        get_network_boxes.restype = POINTER(DETECTION)

        make_network_boxes = lib.make_network_boxes
        make_network_boxes.argtypes = [c_void_p]
        make_network_boxes.restype = POINTER(DETECTION)

        free_detections = lib.free_detections
        free_detections.argtypes = [POINTER(DETECTION), c_int]

        free_batch_detections = lib.free_batch_detections
        free_batch_detections.argtypes = [POINTER(DETNUMPAIR), c_int]

        free_ptrs = lib.free_ptrs
        free_ptrs.argtypes = [POINTER(c_void_p), c_int]

        network_predict = lib.network_predict_ptr
        network_predict.argtypes = [c_void_p, POINTER(c_float)]

        reset_rnn = lib.reset_rnn
        reset_rnn.argtypes = [c_void_p]

        load_net = lib.load_network
        load_net.argtypes = [c_char_p, c_char_p, c_int]
        load_net.restype = c_void_p

        load_net_custom = lib.load_network_custom
        load_net_custom.argtypes = [c_char_p, c_char_p, c_int, c_int]
        load_net_custom.restype = c_void_p

        do_nms_obj = lib.do_nms_obj
        do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        do_nms_sort = lib.do_nms_sort
        do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

        free_image = lib.free_image
        free_image.argtypes = [IMAGE]

        letterbox_image = lib.letterbox_image
        letterbox_image.argtypes = [IMAGE, c_int, c_int]
        letterbox_image.restype = IMAGE

        load_meta = lib.get_metadata
        lib.get_metadata.argtypes = [c_char_p]
        lib.get_metadata.restype = METADATA

        load_image = lib.load_image_color
        load_image.argtypes = [c_char_p, c_int, c_int]
        load_image.restype = IMAGE

        rgbgr_image = lib.rgbgr_image
        rgbgr_image.argtypes = [IMAGE]

        predict_image = lib.network_predict_image
        predict_image.argtypes = [c_void_p, IMAGE]
        predict_image.restype = POINTER(c_float)

        predict_image_letterbox = lib.network_predict_image_letterbox
        predict_image_letterbox.argtypes = [c_void_p, IMAGE]
        predict_image_letterbox.restype = POINTER(c_float)

        network_predict_batch = lib.network_predict_batch
        network_predict_batch.argtypes = [c_void_p, IMAGE, c_int, c_int, c_int,
                                           c_float, c_float, POINTER(c_int), c_int, c_int]
        network_predict_batch.restype = POINTER(DETNUMPAIR)

        def make_c_image(image):
            # Darknet wants the pixel data by plane/channel instead of by pixel.
            # Since our images are b&w, we just get the r channel and repeat it
            # 3 times. FIXME: this is a hack and should be fixed and done properly
            w, h = image.size
            img = lib.make_image(w, h, 3)
            data = [c_float(pixel[0]/255.0) for pixel in image.getdata()]
            data = data + data + data
            img.data = c_array(c_float, data)
            return img

        def classify(net, meta, image):
            should_free = False
            if isinstance(image, PIL.Image.Image):
                im = make_c_image(image)
            else:
                im = load_image(cstr(image), 0, 0)
                should_free = True

            out = predict_image(net, im)
            res = []
            for i in range(meta.classes):
                if self.altNames is None:
                    nameTag = meta.names[i]
                else:
                    nameTag = self.altNames[i]
                res.append((nameTag, out[i]))

            if should_free:
                free_image(im)

            res = sorted(res, key=lambda x: -x[1])
            return res

        self._classify = classify

        def detect(net, meta, image, thresh=.5, hier_thresh=.5, nms=.45, debug= False):
            """
            Performs the meat of the detection
            """
            should_free = False
            if isinstance(image, PIL.Image.Image):
                im = make_c_image(image)
            else:
                #pylint: disable= C0321
                im = load_image(cstr(image), 0, 0)
                for byte in im.data:
                    print(byte)
                should_free = True
                if debug: print("Loaded image")

            ret = detect_image(net, meta, im, thresh, hier_thresh, nms, debug)
            if should_free:
                free_image(im)
                if debug: print("freed image")
            return ret

        self._detect = detect

        def detect_image(net, meta, im, thresh=.5, hier_thresh=.5, nms=.45, debug= False):
            num = c_int(0)
            if debug: print("Assigned num")
            pnum = pointer(num)
            if debug: print("Assigned pnum")
            # predict_image(net, im)
            # letter_box = 0
            predict_image_letterbox(net, im)
            letter_box = 1
            if debug: print("did prediction")
            #dets = get_network_boxes(net, custom_image_bgr.shape[1], custom_image_bgr.shape[0], thresh, hier_thresh, None, 0, pnum, letter_box) # OpenCV
            dets = get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum, letter_box)
            if debug: print("Got dets")
            num = pnum[0]
            if debug: print("got zeroth index of pnum")
            if nms:
                do_nms_sort(dets, num, meta.classes, nms)
            if debug: print("did sort")
            res = []
            if debug: print("about to range")
            for j in range(num):
                if debug: print("Ranging on "+str(j)+" of "+str(num))
                if debug: print("Classes: "+str(meta), meta.classes, meta.names)
                for i in range(meta.classes):
                    if debug: print("Class-ranging on "+str(i)+" of "+str(meta.classes)+"= "+str(dets[j].prob[i]))
                    if dets[j].prob[i] > 0:
                        b = dets[j].bbox
                        if self.altNames is None:
                            nameTag = meta.names[i]
                        else:
                            nameTag = self.altNames[i]
                        if debug:
                            print("Got bbox", b)
                            print(nameTag)
                            print(dets[j].prob[i])
                            print((b.x, b.y, b.w, b.h))
                        res.append((nameTag, dets[j].prob[i], (b.x, b.y, b.w, b.h)))
            if debug: print("did range")
            res = sorted(res, key=lambda x: -x[1])
            if debug: print("did sort")
            free_detections(dets, num)
            if debug: print("freed detections")
            return res

        self.netMain = load_net_custom(configPath, weightPath, 0, 1)  # batch size = 1
        self.metaMain = load_meta(metaPath)
        with open(metaPath) as metaFH:
            metaContents = metaFH.read()
            import re
            match = re.search("names *= *(.*)$", metaContents, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1)
            else:
                result = None
            try:
                if os.path.exists(result):
                    with open(result) as namesFH:
                        namesList = namesFH.read().strip().split("\n")
                        self.altNames = [x.strip() for x in namesList]
            except TypeError:
                pass

    def detect(self, image, thresh= 0.25):
        """
        Returns list of tuples like
            ('obj_label', confidence, (bounding_box_x_px, bounding_box_y_px, bounding_box_width_px, bounding_box_height_px))
            The X and Y coordinates are from the center of the bounding box. Subtract half the width or height to get the lower corner.
        """
        if self.shutupDarknet: suppressed = supress_stdio()
        ret = self._detect(self.netMain, self.metaMain, image, thresh)
        if self.shutupDarknet: restore_stdio(suppressed)
        return ret

    def classify(self, image):
        if self.shutupDarknet: suppressed = supress_stdio()
        ret = self._classify(self.netMain, self.metaMain, image)
        if self.shutupDarknet: restore_stdio(suppressed)
        return ret

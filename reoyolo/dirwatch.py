import pyinotify
from pathlib import Path
import datetime, uuid, os, time
from reoyolo import image_processing, conf, notify
import traceback


def get_output_filename(file_in, output_dir, mkdirs=True):
    myuuid = str(uuid.uuid1()).split('-')[1]  # few bytes of randomness to the filename
    if file_in is None:
        c_time = time.time()
    else:
        c_time = os.stat(file_in).st_ctime
    d = datetime.datetime.fromtimestamp(c_time)
    date_string = "%s/%s/%s/" % (d.year, d.month, d.day)
    folder_out = output_dir + date_string
    if mkdirs:
        Path(folder_out).mkdir(parents=True, exist_ok=True, mode=777)  # recursively make folder, ignore if it already exists
    newfile = "img_" + str(int(c_time)) + myuuid
    return folder_out, newfile


def store_files_and_cuts(img, cuts, original_img, original_filename):
    # Ouput processed file to ouput dir
    processed_folder, processed_file_prefix = get_output_filename(original_filename, conf.OUTPUT_DIR)
    f = processed_folder + processed_file_prefix + ".jpg"
    image_processing.save_image(img, f)

    # move original to original folder
    orig_folder, orig_file_prefix = get_output_filename(original_filename, conf.ORIG_DIR)
    f = orig_folder + orig_file_prefix + ".jpg"
    image_processing.save_image(original_img, f)

    all_labels = []
    # Write cuts to cuts folder
    for i, (cut, label) in enumerate(cuts):
        _, cuts_file_prefix = get_output_filename(original_filename, conf.CUTS_DIR, mkdirs=False)
        Path(conf.CUTS_DIR + label).mkdir(parents=True, exist_ok=True, mode=777)
        f = conf.CUTS_DIR + label + "/" + cuts_file_prefix + str(i) + ".jpg"
        image_processing.save_image(cut, f)
        all_labels.append(label)

    if len(list(enumerate(cuts))) == 1:
        # Write image to notify dir and notify me
        print("only 1 cut - " + label)
        p = 'notify/' + cuts_file_prefix + str(i) + str(uuid.uuid1()).replace("-","") + ".jpg"
        f = conf.NOTIFY_DIR + p
        image_processing.save_image(cut, f)
        notify.notify_img(p, label, all_labels)
    elif len(list(enumerate(cuts))) > 1:
        print("More than one cut, send me the whole photo instead")
        p = 'notify/' + str(uuid.uuid1()).replace("-", "") + ".jpg"
        f = conf.NOTIFY_DIR + p
        image_processing.save_image(img, f)
        notify.notify_img(p, "multiple", all_labels)

    # Delete files older than 1 day from NOTIFY
    for root, _, files in os.walk(conf.NOTIFY_DIR + "notify/"):
        for f in files:
            if os.stat(root + f).st_mtime < time.time() - 1 * 86400:
                os.remove(root + f)
                print("older than a day - deleting file " + str(f))

    print("Done - now deleting")
    if original_filename is not None:
        os.remove(original_filename)

    # Fix permissions for all folder
    for r, d, f in os.walk(conf.OUTPUT_DIR):
        os.chmod(r, 0o777)
    for r, d, f in os.walk(conf.CUTS_DIR):
        os.chmod(r, 0o777)
    for r, d, f in os.walk(conf.ORIG_DIR):
        os.chmod(r, 0o777)



class NewFileHandler(pyinotify.ProcessEvent):
    def __init__(self, processor, watch_manager):
        self.processor = processor
        self.watch_manager = watch_manager
        self.mask = pyinotify.IN_CLOSE_NOWRITE | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE
        self.watch_manager.add_watch(conf.PROCESS_DIR, self.mask)
        self.dir_set = set(conf.PROCESS_DIR)
        for root, subdirs, files in os.walk(conf.PROCESS_DIR):
            if root not in self.dir_set:
                self.dir_set.add(root)
                self.watch_manager.add_watch(root, self.mask)
                print(f"Adding {root} to watcher")
            for s in subdirs:
                subdir = os.path.join(root, s)
                if subdir not in self.dir_set:
                    self.dir_set.add(subdir)
                    self.watch_manager.add_watch(subdir, self.mask)
                    print(f"Adding {subdir} to watcher")



    def process_IN_CREATE(self, event):
        if event.dir:
            print(f"GOT A DIRECTORY CREATE {event}")
            d = event.pathname
            if d in self.dir_set: # already watching this dir
                return
            self.watch_manager.add_watch(d, self.mask)
            self.dir_set.add(d)

    def process_IN_CLOSE_NOWRITE(self, event):
        pass

    def process_IN_CLOSE_WRITE(self, event):
        print(f"New files = {event} ---- {event.path} ---- {event.name} -- {event.dir} ", flush=True)
        if event.dir:
            print("GOT A DIRECTORY")
            return

        filez = event.pathname
        try:
            if Path(filez).stat().st_size == 0:  # Happened once - but it breaks the watchdog thread
                os.remove(filez)
                print("##### ZERO SIZE FILE DELETED!!!!", filez, flush=True)
                return

            # Grab a new image, to be done after the new file
            # Run opencv on new file
            original_img, img, labels, confidences, cuts = self.processor.file_process(filez, confidence_level=0)
            store_files_and_cuts(img, cuts, original_img, event.pathname)
        except:
            traceback.print_exc() # Not much we can do, just continue
            return


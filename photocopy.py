# -*- coding: utf-8 -*-

import argparse, os, sys, datetime, shutil



class PhotoCopy:
    # Default names - can be overriden with ini file
    month_to_path = {
        1 : '01 Januari',
        2 : '02 Februari',
        3 : '03 Mars',
        4 : '04 April',
        5 : '05 Maj',
        6 : '06 Juni',
        7 : '07 Juli',
        8 : '08 Augusti',
        9 : '09 September',
        10: '10 Oktober',
        11: '11 November',
        12: '12 December'
    }

    # Status constants
    STAT_COPY     = 'Copied'
    STAT_EXISTED  = 'Already Existed'
    STAT_FAILED   = 'Failed'
    STAT_FINISHED = 'Finished'
    STAT_UNHANDLED = 'Unhandled' # Only used internally

    def __init__(self, src, dst, ini = 'photocopy.ini'):
        self.src = src
        self.dst = dst
        self.files = []
        self.__load_ini(ini)

        # Save all files to copy and figure out destination path
        for root, _ ,files in os.walk(src):
            for file in files:
                src_path = os.path.join(root,file)

                # Figure out dst path
                ctime = os.path.getmtime(src_path)
                cdt = datetime.datetime.fromtimestamp(ctime)
                dst_path = os.path.join(dst, str(cdt.year), self.month_to_path[cdt.month], file)

                self.files.append({
                    'src' : src_path,
                    'dst' : dst_path,
                    'status' : PhotoCopy.STAT_UNHANDLED
                })
        
        # Sort and set index
        self.files = sorted(self.files, key=lambda x: x['src'])

        # Reset stats - use counters for efficiency
        self.__reset_stats()
    
    def __load_ini(self, ini):
        full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ini)
        if os.path.exists(full_path) : 
            conf = {}
            with open(full_path, 'r') as file:
                for line in file:
                    if len(line) > 0 and line[0] != '#':
                        parts = line.split('=')
                        if len(parts) == 2:
                            conf[parts[0].strip()] = parts[1].strip()
            # Configure months
            for i, key in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', \
                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                if key in conf: 
                    self.month_to_path[i + 1] = conf[key]

    def __reset_stats(self):
        self.nbr_files = len(self.files)
        self.nbr_copied = 0
        self.nbr_existed = 0
        self.nbr_failed = 0
        self.index = 0
        self.last_error = None

    def reset_to_failed(self):
        ''' Use to retry copy failed files, will set src_paths to faled '''
        self.files = [d for d in self.files if d['status'] == PhotoCopy.STAT_FAILED]
        for file in self.files: file['status'] = PhotoCopy.STAT_UNHANDLED

        # Reset stats - use counters for efficiency
        self.__reset_stats()

    def get_nbr_files(self):
        return self.nbr_files  

    def get_nbr_files_left(self):
        return self.nbr_files - self.index
    
    def get_nbr_copied(self):
        return self.nbr_copied
    
    def get_nbr_existed(self):
        return self.nbr_existed
    
    def get_nbr_failed(self):
        return self.nbr_failed 
    
    def get_copied_files(self):
        return [d['src'] for d in self.files if d['status'] == PhotoCopy.STAT_COPY]
    
    def get_existed_files(self):
        return [d['src'] for d in self.files if d['status'] == PhotoCopy.STAT_EXISTED]
    
    def get_failed_files(self):
        return [d['src'] for d in self.files if d['status'] == PhotoCopy.STAT_FAILED]
    
    def get_last_error(self):
        return self.last_error 
    
    def get_next_file(self, remove_src_dst = True):
        if self.index >= len(self.files):
            return ('','')
        src_path = self.files[self.index]['src']
        dst_path = self.files[self.index]['dst']
        if remove_src_dst:
            if src_path.startswith(self.src):
                src_path = src_path[len(self.src) + 1:]
            if dst_path.startswith(self.dst):
                dst_path = dst_path[len(self.dst) + 1:]
        return (src_path, dst_path)
    
    def copy_next(self):
        if self.index >= self.nbr_files:
            return PhotoCopy.STAT_FINISHED
        
        f = self.files[self.index]
        self.index += 1

        if os.path.isfile(f['dst']):
            f['status'] = PhotoCopy.STAT_EXISTED
            self.nbr_existed += 1
            return PhotoCopy.STAT_EXISTED
        else:
            try:
                os.makedirs(os.path.dirname(f['dst']), exist_ok=True)
                shutil.copy2(f['src'], f['dst'])
                f['status'] = PhotoCopy.STAT_COPY
                self.nbr_copied += 1
                return PhotoCopy.STAT_COPY
            except Exception as e:
                f['status'] = PhotoCopy.STAT_FAILED
                self.nbr_failed += 1
                self.last_error = e
                return PhotoCopy.STAT_FAILED
    
    # Value between 0 - 100
    def get_progress(self):
        if self.nbr_files == 0:
            return 100
        return int((self.index / self.nbr_files) * 100.0)

class ProgressBar:
    def __init__(self, max_value = 100):
        steps = 7 * 10
        self.step_size = max_value / steps
        self.step_current = 0
        self.refresh()

    def refresh(self):
        print('|  10% |  20% |  30% |  40% |  50% |  60% |  70% |  80% |  90% | 100% |')
        print('*' + '*' * (self.step_current), end='')
        sys.stdout.flush() 
    
    def update(self, current_value):
        step_current = int(current_value / self.step_size)
        if step_current > self.step_current:
            print('*' * (step_current - self.step_current), end='')
            sys.stdout.flush() 
            self.step_current = step_current

def main():
    parser = argparse.ArgumentParser(description='Copy photo to year month structure')
    parser.add_argument('src', help='Source directory')
    parser.add_argument('dst', help='Destination directory')
    args = vars(parser.parse_args())

    pc = PhotoCopy(args['src'], args['dst'])

    while True:

        # Setup progress bar
        print('Files to copy:', pc.get_nbr_files())  
        print()  
        progress_bar = ProgressBar()

        # Start copy
        while pc.copy_next() != PhotoCopy.STAT_FINISHED:
            progress_bar.update(pc.get_progress())

        # Summarize result
        print()
        print()
        print(f'{pc.get_nbr_copied()} of {pc.get_nbr_files()} files copied')
        if (pc.get_nbr_existed() > 0):
            print(f'{pc.get_nbr_existed()} of {pc.get_nbr_files()} files already existed')
        if (pc.get_nbr_failed() > 0):
            print(f'{pc.get_nbr_failed()} of {pc.get_nbr_files()} files failed')

        full_report = input('View full report? [y/N]: ') 
        if full_report.lower() == 'y':
            print()
            print('-------------------------------------------------------------------------------')
            print('|                                FILES COPIED                                 |')
            print('-------------------------------------------------------------------------------')
            for file in sorted(pc.get_copied_files()):
                print(file)
            print()
            print('-------------------------------------------------------------------------------')
            print('|                           FILES ALREADY EXISTED                             |')
            print('-------------------------------------------------------------------------------')
            for file in sorted(pc.get_existed_files()):
                print(file)
            print()
            print('-------------------------------------------------------------------------------')
            print('|                                FILES FAILED                                 |')
            print('-------------------------------------------------------------------------------')
            for file in sorted(pc.get_failed_files()):
                print(file)
            print('')
        
        exit_loop = True
        if (pc.get_nbr_failed() > 0):
            retry_failed = input('Do you want to retry failed files? [y/N]: ') 
            if retry_failed.lower() == 'y':
                exit_loop = False
                pc.reset_to_failed()
        if exit_loop:
            break








if __name__ == '__main__':
    main()    
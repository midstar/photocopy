from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from photocopy import PhotoCopy

import threading, time

###############################################################################
# Create root

root = Tk()

###############################################################################
# Globals

str_src = StringVar()
str_dst = StringVar()
progress = IntVar()
running = False
pc = None
thread = None
start_time = None

###############################################################################
# Helpers

def update_stats():
    if pc == None:
        return
    
    lbl_total_val.config(text=str(pc.get_nbr_files()))
    lbl_left_val.config(text=str(pc.get_nbr_files_left()))
    lbl_copied_val.config(text=str(pc.get_nbr_copied()))
    lbl_existed_val.config(text=str(pc.get_nbr_existed()))
    lbl_failed_val.config(text=str(pc.get_nbr_failed()))
    
    # Estimate remaining time
    files_done = pc.get_nbr_files() -  pc.get_nbr_files_left()
    time_elapsed = time.time() - start_time
    time_per_file = 0 if files_done== 0 else time_elapsed / files_done
    time_left = time_per_file * pc.get_nbr_files_left()
    minutes = 0 if time_left < 60 else int(time_left / 60)
    seconds = int(time_left - minutes * 60)
    if minutes > 0:
        time_txt = f'{minutes}m {seconds}s'
    else:
        time_txt = f'{seconds}s'
    lbl_time_val.config(text=time_txt)

    progress.set(pc.get_progress())
    root.update()

###############################################################################
# Call backs

def cb_select_src():
    src_path = filedialog.askdirectory(title = 'Source directory')
    if src_path != '' : str_src.set(src_path)

def cb_select_dst():
    dst_path = filedialog.askdirectory(title = 'Destination directory')
    if dst_path != '' :  str_dst.set(dst_path)

def cb_run_stop():
    global pc
    global running
    global thread
    global start_time

    if running:
        running = False # Thread will die
        btn_run_stop.config(text='Wait')
        return

    if str_src.get() == '' or str_dst.get() == '':
        messagebox.showerror(title='Error', message='Invalid source or dest')
        return

    rerun = 'no'
    if pc != None and pc.get_nbr_failed() > 0:
        rerun = messagebox.askquestion(title='Rerun failed', message='Do you want to re-run only failed files?')

    if rerun == 'yes':
        pc.reset_to_failed()
    else:
        pc = PhotoCopy(str_src.get(), str_dst.get())
    start_time = time.time()
    update_stats()
    src_all.delete('1.0', END)
    src_copied.delete('1.0', END)
    src_existed.delete('1.0', END)
    src_failed.delete('1.0', END)
    running = True
    btn_run_stop.config(text='Stop')
    thread = threading.Thread(target=thrd_copy)
    thread.start()

###############################################################################
# Threads

def thrd_copy():
    global pc
    global running
    
    while running:
        src_path, dst_path = pc.get_next_file()
        tag = str(hash(src_path))
        if src_path != '':
            src_all.insert(INSERT, f'{src_path} > {dst_path}\n', tag)
        src_all.see(END)
        status = pc.copy_next()
        if status == PhotoCopy.STAT_FINISHED:
            break # We are done
        if status == PhotoCopy.STAT_EXISTED:
            src_existed.insert(INSERT, f'{src_path} > {dst_path}\n', tag)
            src_existed.see(END)
            color = 'blue'
        elif status == PhotoCopy.STAT_FAILED:
            src_failed.insert(INSERT, f'{src_path} > {dst_path}\n', tag)
            src_failed.insert(INSERT, f'  {pc.get_last_error()}\n', tag)
            src_failed.see(END)
            src_all.insert(INSERT, f'  {pc.get_last_error()}\n', tag)
            src_all.see(END)
            color = 'red'
        else:
            src_copied.insert(INSERT, f'{src_path} > {dst_path}\n', tag)
            src_copied.see(END)
            color = 'green'

        src_all.tag_config(tag, foreground=color)
        src_copied.tag_config(tag, foreground=color)
        src_existed.tag_config(tag, foreground=color)
        src_failed.tag_config(tag, foreground=color)
        update_stats()

    btn_run_stop.config(text='Run')
    running = False
    

###############################################################################
# UI Setup

root.geometry('1400x700')
root.title('Photo Copy')

# Top bar
frm_top = Frame(root)
frm_top.pack(fill=X)

# Source and Dest
frm_src_dst = Frame(frm_top)
frm_src_dst.pack(side=LEFT, fill=X, expand=True)

# Source
frm_src = Frame(frm_src_dst)
frm_src.pack(fill=X)

lbl_src = Label(frm_src, text ='Source', width = 6) 
lbl_src.pack(side=LEFT)
entry_src = Entry(frm_src,textvariable = str_src, font=('calibre',10,'normal'))
entry_src.pack(side=LEFT, fill=X, expand=True)
btn_select_src = Button(frm_src, text ='Select', command = cb_select_src)
btn_select_src.pack(side=RIGHT, padx=2)

# Destination
frm_dst = Frame(frm_src_dst)
frm_dst.pack(fill=X)

lbl_dst = Label(frm_dst, text ='Dest', width = 6) 
lbl_dst.pack(side=LEFT)
entry_dst = Entry(frm_dst,textvariable = str_dst, font=('calibre',10,'normal'))
entry_dst.pack(side=LEFT, fill=X, expand=True)
btn_select_dst = Button(frm_dst, text ='Select', command = cb_select_dst)
btn_select_dst.pack(side=LEFT, padx=2)

# Run / stop button
fnt_large = font.Font(family='Helvetica', size=20, weight=font.BOLD)
btn_run_stop = Button(frm_top, text ='Run', command = cb_run_stop, font=fnt_large, width=5)
btn_run_stop.pack(side=LEFT, padx=5)


# Stats
frm_stats = Frame(frm_top)
frm_stats.pack(side=RIGHT)

frm_stats1 = Frame(frm_stats)
frm_stats1.pack(fill=X)

frm_stats2 = Frame(frm_stats)
frm_stats2.pack(fill=X)

frm_stats3 = Frame(frm_stats)
frm_stats3.pack(fill=X)

fnt_small = font.Font(family='Helvetica', size=7)

frm_total = Frame(frm_stats1)
frm_total.pack(side=LEFT)
lbl_total = Label(frm_total, text ='Total:', font=fnt_small, anchor = 'e', width = 7) 
lbl_total.pack(side=LEFT)
lbl_total_val = Label(frm_total, text ='0', font=fnt_small, width = 8) 
lbl_total_val.pack(side=RIGHT)

frm_left = Frame(frm_stats1)
frm_left.pack(side=RIGHT)
lbl_left = Label(frm_left, text ='Left:', font=fnt_small, anchor = 'e', width = 7) 
lbl_left.pack(side=LEFT)
lbl_left_val = Label(frm_left, text ='0', font=fnt_small, width = 8) 
lbl_left_val.pack(side=RIGHT)

frm_copied = Frame(frm_stats2)
frm_copied.pack(side=LEFT)
lbl_copied = Label(frm_copied, text ='Copied:', font=fnt_small, anchor = 'e', width = 7)  
lbl_copied.pack(side=LEFT)
lbl_copied_val = Label(frm_copied, text ='0', font=fnt_small, width = 8)  
lbl_copied_val.pack(side=RIGHT)

frm_existed = Frame(frm_stats2)
frm_existed.pack(side=RIGHT)
lbl_existed = Label(frm_existed, text ='Existed:', font=fnt_small, anchor = 'e', width = 7)
lbl_existed.pack(side=LEFT)
lbl_existed_val = Label(frm_existed, text ='0', font=fnt_small, width = 8)
lbl_existed_val.pack(side=RIGHT)

frm_failed = Frame(frm_stats3)
frm_failed.pack(side=LEFT)
lbl_failed = Label(frm_failed, text ='Failed:', font=fnt_small, anchor = 'e', width = 7)
lbl_failed.pack(side=LEFT)
lbl_failed_val = Label(frm_failed, text ='0', font=fnt_small, width = 8)
lbl_failed_val.pack(side=RIGHT)

frm_time = Frame(frm_stats3)
frm_time.pack(side=RIGHT)
lbl_time = Label(frm_time, text ='Time:', font=fnt_small, anchor = 'e', width = 7)
lbl_time.pack(side=LEFT)
lbl_time_val = Label(frm_time, text ='', font=fnt_small, width = 8)
lbl_time_val.pack(side=RIGHT)

# Progress bar
progressbar = ttk.Progressbar(variable = progress)
progressbar.pack(fill=X, padx = 5, pady = 5)

# Status log entries
tab_parent = ttk.Notebook(root)
tab_all = ttk.Frame(tab_parent)
tab_copied = ttk.Frame(tab_parent)
tab_existed= ttk.Frame(tab_parent)
tab_failed = ttk.Frame(tab_parent)
tab_parent.add(tab_all, text='All')
tab_parent.add(tab_copied, text='Copied')
tab_parent.add(tab_existed, text='Already existed')
tab_parent.add(tab_failed, text='Failed')

src_all = ScrolledText(tab_all)
src_all.pack(fill=BOTH, expand = True)

src_copied = ScrolledText(tab_copied)
src_copied.pack(fill=BOTH, expand = True)

src_existed = ScrolledText(tab_existed)
src_existed.pack(fill=BOTH, expand = True)

src_failed = ScrolledText(tab_failed)
src_failed.pack(fill=BOTH, expand = True)

tab_parent.pack(fill=BOTH, expand = True)

root.mainloop()
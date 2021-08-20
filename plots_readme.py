import shutil, os
dst = article_image_folder = r'./images'

def run_cmd_FontAsPath(src):
    path2figure, fname = os.path.split(src)
    # print(path2figure, fname)
    fname_no_suffix = fname[:-4]
    cmd = rf'''"D:\Program Files\gs\gs9.54.0\bin\gswin64.exe" -o {fname_no_suffix}-FontAsPath.pdf -dNoOutputFonts -sDEVICE=pdfwrite {fname_no_suffix}.pdf '''
    print(cmd)
    os.system(f'cd "{path2figure}" && {cmd}')
    return path2figure + '/' + fname_no_suffix + '-FontAsPath.pdf'


if True:
    ''' 
    软件：AxGlyph
    源文件：aaa.agx
    说明：## 框图
    '''
    src = r"D:\DrH\demo\Newfolder\805-0700-slessinv-Vdc-0.pdf"
    src = run_cmd_FontAsPath(src)
    shutil.copy(src, dst)

    src = r"D:\DrH\demo\Newfolder\Untitled.pdf"
    shutil.copy(src, dst)


import os
import xlwings as xw
import numpy as np
import pandas as pd
from sklearn import linear_model
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib as mpl

class File:
    
    def __init__(self, dirpath, fname):
        self.dirpath = dirpath
        self.fname = fname
        self.fpath = os.path.join(self.dirpath, self.fname)
        
#     @property
#     def fpath(self):
#         return self.fpath 
    
#     @fpath.setter    
#     def fpath(self, input_fpath):
#         if input_fpath != "":
#             self.fpath = input_fpath
            
    def get_value(self):
        self.book = xw.Book(self.fpath)
        self.sheets = self.book.sheets
        
#     def save_to_newfile(self):
        
class original_Exfile(File):
    
    def __init__(self, dirpath, fname, m, n):
        super().__init__(dirpath, fname)
        self.m = m
        self.n = n
#         print("self.fpath: {}".format(self.fpath))
        
    def get_value(self):
        super().get_value()
        sheet2 = self.sheets[1]
        print("sheet2.name: {}".format(sheet2.name))
        river_num = int(sheet2.range("B1").value)
        mmin = sheet2.range("B3").value
        mmax = sheet2.range("C3").value
        miter = sheet2.range("D3").value
        nmin = sheet2.range("B4").value
        nmax = sheet2.range("C4").value
        niter = sheet2.range("D4").value

        ms = np.array(np.arange(mmin, mmax+miter, miter)*100, dtype=int)
        ns = np.array(np.arange(nmin, nmax+miter, niter)*100, dtype=int)
        print(ms, ns)
        loc_tm = int(np.where(ms == int(self.m*100))[0][0]) + 1
        loc_tn = int(np.where(ns == int(self.n*100))[0][0]) + 1

        try:
            sname = "n=" + str(self.n)
            target_sheet = self.sheets[sname]
        except:
            print("there no sheet which name is (n={})".format(self.n))

        usecols = list(range((loc_tm-1)*3*river_num, (loc_tm)*3*river_num))
        print(usecols)
        df_sheet = pd.read_excel(self.fpath, target_sheet.name, index_col=None, header=1, usecols=usecols)
        df_sheet = df_sheet.dropna(how="all", axis=1)
        df_sheet = df_sheet.drop([0])
        # column名を変更する。
        mainSt = df_sheet.columns[0][:-4]
        columns = []
        for i in range(0, len(df_sheet.columns)):
            if i % 2 == 0:
                # chiの格納された列の場合（偶数列目）
                # indexが０から始まる事に注意
                if i == 0:
                    name = "χ_" + mainSt + "本流"
                    columns.append(name)
                else:
                    name = "χ_" + mainSt + df_sheet.columns[i]
                    columns.append(name)
            else:
                # zの格納された列の場合（奇数列目）
                if i == 1:
                    name = "Z_" + mainSt + "本流"
                    columns.append(name)
                else:
                    name = "Z_" + mainSt + df_sheet.columns[i-1]
                    columns.append(name)
        df_sheet.set_axis(columns, axis=1, inplace=True)
        self.book.close()
        
        return df_sheet
    
class chi_compiler:
    
    def __init__(self, dirpath, m, n):
        self.dirpath = dirpath
        self.m = m
        self.n = n
        self.outfname = "compiled_m=" + str(self.m) + "_n=" + str(self.n) + ".xlsx"
        self.outpath = os.path.join(self.dirpath, self.outfname)
        
    def compile_specific_mn(self):
        i = 0
        for curDir, dirs, files in os.walk(self.dirpath):
            for file in files:
                if file.startswith("Chiplot"):
                    print("now: {}".format(file))
                    chifile = original_Exfile(curDir, file, self.m, self.n)
                    if i == 0:
                        df = chifile.get_value()
                    else:
                        df = pd.concat([df, chifile.get_value()], axis=1)
                i+=1
                
        newcolumns = []
        for i in range(0, len(df.columns), 2):
            newcolumns.append("R"+str(int(i/2))+"_"+df.columns[i])
            newcolumns.append("R"+str(int(i/2))+"_"+df.columns[i+1])
                
        df.set_axis(newcolumns, axis=1, inplace=True)
        
        self.df = df
        
    def save_to_newfile(self):
        self.df.to_excel(self.outpath, sheet_name="chi_z", index=False)
        
class compiled_Exfile(File):
    
    def __init__(self, dirpath, fname):
        super().__init__(dirpath, fname)
    
    def get_value(self):
        super().get_value()
        sheet = self.sheets["chi_z"]
        self.df = pd.read_excel(self.fpath, sheet.name, index_col=None)
        self.book.close()
        
    def chi_plot(self):
        p_fpath = self.fpath[:-5]
#         mpl.rcParams['axes.grid'] = True
#         mpl.rcParams['axes.titlesize'] = 17
        plt.rcParams["font.family"] = "Times New Roman"
        plt.rcParams["xtick.minor.visible"] = True #x軸補助目盛りの追加
        plt.rcParams["ytick.minor.visible"] = True #y軸補助目盛りの追加
        plt.rcParams['xtick.direction'] = 'in'#x軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
        plt.rcParams['ytick.direction'] = 'in'#y軸の目盛線が内向き('in')か外向き('out')か双方向か('inout')
        plt.rcParams["xtick.major.width"] = 2 #X軸の主目盛の太さ
        plt.rcParams["ytick.major.width"] = 2 #Y軸の主目盛の太さ
        plt.rcParams["xtick.minor.width"] = 1.2 #X軸の副目盛の太さ
        plt.rcParams["ytick.minor.width"] = 1.2 #Y軸の副目盛の太さ
        plt.rcParams["xtick.major.size"] = 10 #X軸の主目盛の長さ
        plt.rcParams["ytick.major.size"] = 10 #Y軸の主目盛の長さ
        plt.rcParams["xtick.minor.size"] = 5 #X軸の副目盛の長さ
        plt.rcParams["ytick.minor.size"] = 5 #Y軸の副目盛の長さ
        plt.rcParams["xtick.labelsize"] = 14.0 #X軸の目盛りラベルのフォントサイズ
        plt.rcParams["ytick.labelsize"] = 14.0 #Y軸の目盛ラベルのフォントサイズ
#         plt.rcParams['font.size'] = 15 #フォントの大きさ
        plt.rcParams['xtick.top'] = False #x軸の上部目盛り
        plt.rcParams['ytick.right'] = False #y軸の右部目盛り
        plt.rcParams['axes.linewidth'] = 2# 軸の線幅edge linewidth。囲みの太さ
        fig = plt.figure(figsize=(10, 7)) #figsize=(70, 10)
    #     ax_chi = fig.add_subplot(1, 1, 1)
    #     ax_reg = fig.add_subplot(1, 1, 1)
        iterNum = int(self.df.shape[1] / 2)
        for i in range(iterNum):
            river_id = self.df.columns[i*2][:2]
            chi = self.df.iloc[:, 2*i].to_numpy()
            z = self.df.iloc[:, 2*i+1].to_numpy()
            nan_row = np.where(np.isnan(chi))[0]
            if len(nan_row) != 0:
                chi = chi[:nan_row[0]]
                z = z[:nan_row[0]]
#                 z_reg = coefs[i]*chi
                plt.plot(chi, z, color=cm.gnuplot(1-i/iterNum), label=river_id) #, 
#                 plt.plot(chi, z_reg, color=cm.gnuplot(1-i/iterNum))
            else:
#                 z_reg = coefs[i]*chi
                plt.plot(chi, z, color=cm.gnuplot(1-i/iterNum), label=river_id)
#                 plt.plot(chi, z_reg, color=cm.gnuplot(1-i/iterNum))

        plt.xlabel("chi [m]", fontsize=20)
        plt.ylabel("z [m]", fontsize=20)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=6)
#         plt.title("m="+m+" n="+n)

    #     fig.subplots_adjust(hspace=0.5, wspace=0.2)

        plt.show()

        plt.style.use('seaborn-white')
    #     plt.grid(linestyle='None')
        fig.savefig(p_fpath + ".png", bbox_inches='tight')
        fig.clear()
        plt.close(fig)
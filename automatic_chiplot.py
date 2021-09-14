import xlwings as xw
import os
import numpy as np
import pandas as pd
from sklearn import linear_model
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib as mpl

class automation:
    
    def __init__(self):
        
        pass
        
    def Do_chimacro_on_fiels(self, path1, path2, input_nm):

        """
        複数のファイルのχプロットマクロ、決定係数マクロ、グラフコンパイルマクロを自動実行するための関数。


        引数；
        保存先のディレクトリ(path1)、元ファイルがあるディレクトリ(path2), 設定するmとnのリストを要素としてもつ辞書（input_nm)      

        """

    #     （例）
    #     path_1 = r"C:\Users\miyar\OneDrive\デスクトップ\四年\VBA\automation\m03_n08"
    #     path_2 = r"C:\Users\miyar\OneDrive\デスクトップ\四年\VBA\automation\none_nahari"
    #     input_nm = {"m_setting" : [0.3, 0.4, 0.1],
    #                 "n_setting" : [0.7, 0.9, 0.1]}     

        files = os.listdir(path_2)

        for filename in files:
            print("now donig" + filename)
            total_path = path_2 + "\\" + filename
            wb = xw.Book(total_path)
            save_pathname = path_1 + "\\" + filename
            wb.save(save_pathname)
            wb.close()

            wb_2 = xw.Book(save_pathname)
            shts = wb_2.sheets
            delsht_name = []
            for i in shts:
                if i.name != "Sheet1" and i.name != "Sheet2":
                    delsht_name.append(i.name)

            for i in range(len(delsht_name)):
                wb_2.sheets[delsht_name[i]].delete()

            sht2 = wb_2.sheets['Sheet2']
            sht2.range("B3").value = list(input_nm.values())[0]
            sht2.range("B4").value = list(input_nm.values())[1]

            # χプロットを作成するマクロ
            macro_chi = wb_2.macro("ChiMulti2")
            macro_chi()

            # すべての河川、m・n組み合わせでの決定係数を一覧表示するためのマクロ
            macro_R2 = wb_2.macro("Calc_R2")
            macro_R2()

            # すべての χプロットを1つのシート内に配置するためのマクロ
            macro_graph = wb_2.macro("chartCP")
            macro_graph()
            wb_2.save()
            wb_2.close()


    def extract_chi_z(self, fname, **kwargs):

        """

        特定のm, nでのχパラメータと標高値データをχプロットExcelファイルから抽出する関数
        返り値は抽出したデータのpd.Dataframe。

        引数 : 対象のExcelファイル名（拡張子込み）＋　以下の値を要素として持つ辞書

        ・対象のExcelファイルのあるディレクトリの絶対パス（dirpath）
        ・抽出するm (m)
        ・抽出するn (n)

        """

        dirpath = kwargs["dirpath"]
        target_m = kwargs["m"]
        target_n = kwargs["n"]
    #     fname = "Chiplot-NonegawaArea" + ".xlsm"
        fpath = os.path.join(dirpath, fname)
        book = xw.Book(fpath)
        sheets = book.sheets
        sheet2 = sheets[1]
        river_num = int(sheet2.range("B1").value)
        mmin = sheet2.range("B3").value
        mmax = sheet2.range("C3").value
        miter = sheet2.range("D3").value
        nmin = sheet2.range("B4").value
        nmax = sheet2.range("C4").value
        niter = sheet2.range("D4").value

        ms = np.array(np.arange(mmin, mmax+miter, miter)*100, dtype=int)
        ns = np.array(np.arange(nmin, nmax+miter, niter)*100, dtype=int)
        loc_tm = int(np.where(ms == int(target_m*100))[0][0]) + 1
        loc_tn = int(np.where(ns == int(target_n*100))[0][0]) + 1

        try:
            sname = "n=" + str(target_n)
            target_sheet = sheets[sname]
        except:
            print("there no sheet which name is (n={})".format(target_n))


        # print(type(loc_tm), loc_tn)
        # print((loc_tm-1))
        usecols = list(range((loc_tm-1)*3*river_num, (loc_tm)*3*river_num))
        # print(len(usecols))
        df_sheet = pd.read_excel(fpath, target_sheet.name, index_col=None, header=1, usecols=usecols)
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
        # target_m
        book.close()

        return df_sheet

    def compile_specific_mn(self, **kwargs):

        dirpath = kwargs["dirpath"]
        target_m = kwargs["m"]
        target_n = kwargs["n"]
        i = 0
        for curDir, dirs, files in os.walk(dirpath):
            for file in files:
                if file.startswith("Chiplot"):
                    print("now: {}".format(file))
                    if i == 0:
                        df = self.extract_chi_z(file, **kwargs)
                    else:
                        df = pd.concat([df, self.extract_chi_z(file, **kwargs)], axis=1)
                i+=1

        return df

    def save_to_newfile(self, **kwargs):

        dirpath = kwargs["dirpath"]
        m = kwargs["m"]
        n = kwargs["n"]
        df = self.compile_specific_mn(**kwargs)
        fname = "compiled_m=" + str(m) + "_n=" + str(n) + ".xlsx"
        fpath = os.path.join(dirpath, fname)
        print(fpath)
        df.to_excel(fpath, sheet_name="chi_z", index=False)


    def value_from_compiled_file(self, fname, **kwargs):

        dirpath = kwargs["dirpath"]
        fpath = os.path.join(dirpath, fname)
        book = xw.Book(fpath)
        sheets = book.sheets
        sheet = sheets[0]
        df_sheet = pd.read_excel(fpath, sheet.name, index_col=None)
        book.close()

        return df_sheet


    def LinearRegression(self, df_sheet):

        clf = linear_model.LinearRegression(fit_intercept=False)

        coefs = []
        r2s = []
        for i in range(0, df_sheet.shape[1], 2):
        #     print(i)
            chi = df_sheet.iloc[:, i].to_numpy()
            z = df_sheet.iloc[:, i+1].to_numpy()
            nan_row = np.where(np.isnan(chi))[0]
            if len(nan_row) != 0:
                chi = chi[:nan_row[0]].reshape(-1, 1)
                z = z[:nan_row[0]]
                clf.fit(chi, z)
                coefs.append(clf.coef_[0])
                r2s.append(clf.score(chi, z))
            else:
        #         chi.reshape(-1, 1)
                clf.fit(chi.reshape(-1, 1), z)
                coefs.append(clf.coef_[0])
                r2s.append(clf.score(chi.reshape(-1, 1), z))
        
        coefs = np.array(coefs)
        r2s = np.array(r2s)
        
        return coefs, r2s

    def compiled_chiplot(self, df_sheet, coefs, **kwargs):

        dirpath = kwargs["dirpath"]
        m = str(kwargs["m"])
        n = str(kwargs["n"])
        fname = "compiled_chiplot_m="+m+"_n="+n
        fpath = os.path.join(dirpath, fname)
        mpl.rcParams['font.size'] = 10
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['axes.titlesize'] = 17
        fig = plt.figure(figsize=(10, 7)) #figsize=(70, 10)
    #     ax_chi = fig.add_subplot(1, 1, 1)
    #     ax_reg = fig.add_subplot(1, 1, 1)
        iterNum = len(coefs)
        for i in range(iterNum):
            if i == 0:
                river = df_sheet.columns[i*2]
            else: 
                river = df_sheet.columns[i*2][:-2]
    #         print("river: {}".format(river))
            chi = df_sheet.iloc[:, 2*i].to_numpy()
            z = df_sheet.iloc[:, 2*i+1].to_numpy()
            nan_row = np.where(np.isnan(chi))[0]
            if len(nan_row) != 0:
                chi = chi[:nan_row[0]]
                z = z[:nan_row[0]]
                z_reg = coefs[i]*chi
                plt.plot(chi, z, color=cm.gnuplot(1-i/iterNum)) #, label=river
                plt.plot(chi, z_reg, color=cm.gnuplot(1-i/iterNum))
            else:
                z_reg = coefs[i]*chi
                plt.plot(chi, z, color=cm.gnuplot(1-i/iterNum))
                plt.plot(chi, z_reg, color=cm.gnuplot(1-i/iterNum))

    #     ax_chi.set_title("m="+m+" n="+n)
    #     ax_chi.set_xlabel("chi [m]")
    #     ax_chi.set_ylabel("z [m]")
    #     ax_chi.legend()

        plt.xlabel("x")
        plt.ylabel("z")
        plt.title("m="+m+" n="+n)

    #     fig.subplots_adjust(hspace=0.5, wspace=0.2)

        plt.show()

        plt.style.use('seaborn-white')
    #     plt.grid(linestyle='None')
        fig.savefig(fpath + ".png", bbox_inches='tight')
        fig.clear()
        plt.close(fig)
        
        
    def calc_kb(self, coefs, U0, A0, **kwargs):

        U0 = U0 / (365*24*3600* 10**3)
        A0 = A0 * 100
        m = kwargs["m"]
        n = kwargs["n"]
        temp = (coefs**n)*(A0**m)
        kb = U0 / temp

        return kb
    
    def make_columns_name(self, df_sheet):
        
        columns_name = []
        for i in range(len(df_sheet.columns)):
#             print(df_sheet.columns[i][2:])
            if i % 2 == 0:
                columns_name.append(df_sheet.columns[i][2:])
                
        return columns_name
    
    def save_kb_coef_r2(self, kb, coefs, r2s, columns_name, **kwargs):
        
        dirpath = kwargs["dirpath"]
        m = kwargs["m"]
        n = kwargs["n"]
        fname = "compiled_m=" + str(m) + "_n=" + str(n) + ".xlsx"
        fpath = os.path.join(dirpath, fname)
        print(os.path.exists(fpath))
        
        if os.path.exists(fpath):
            data = np.stack([kb, coefs, r2s])
    #         print(data)
            df = pd.DataFrame(data, index=["kb", "coef", "r2"])
            df.set_axis(columns_name, axis=1, inplace=True)

            with pd.ExcelWriter(fpath, mode="a", engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="kb-coef-r2")

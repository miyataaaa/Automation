import xlwings as xw
import os

#保存先のディレクトリ
path_1 = r"C:\Users\miyar\OneDrive\デスクトップ\四年\VBA\automation\m075_n195"
#元ファイルがあるディレクトリ
path_2 = r"C:\Users\miyar\OneDrive\デスクトップ\四年\VBA\automation\none_nahari"
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


    input_nm = {"m_setting" : [0.7, 0.8, 0.05],
                "n_setting" : [1.85, 1.95, 0.05]
                }

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









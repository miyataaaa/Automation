#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# %%time

from osgeo import gdal
from osgeo import gdalconst
import struct
import numpy as np
import math
import os

class InputFile:
	def __init__(self, fname):
		self.fname = fname
		self.inData = gdal.Open(self.fname, gdal.GA_ReadOnly)
		self.cols = self.inData.RasterXSize
		self.rows = self.inData.RasterYSize
		self.bands = self.inData.RasterCount
		self.driver = self.inData.GetDriver()
		self.band = self.inData.GetRasterBand(1)
		self.BandType = gdal.GetDataTypeName(self.band.DataType)
		self.noDataValue = self.band.GetNoDataValue()
		self.geotransform = self.inData.GetGeoTransform()
		self.originX = self.geotransform[0]
		self.originY = self.geotransform[3]
		self.pixelWidth = self.geotransform[1]
		self.pixelHeight = self.geotransform[5]
		self.dataArr = self.band.ReadAsArray(0, 0, self.inData.RasterXSize, self.inData.RasterYSize).astype(np.float64) #This is a data list (i.e., array).

class makeGeoTiff:
	def __init__(self, inFile, outArr, newNoDataValue, outFilePath):#inFile is an instance of InputFile
		# if bandtype == 'Float32'
		self.outFi = inFile.driver.Create(outFilePath, inFile.cols, inFile.rows, 1, gdal.GDT_Float32)
		if self. outFi is None:
    			print ("Could not create surfRough.tif")
    			sys.exit(1)
		self.outBand = self.outFi.GetRasterBand(1)
# write the data
		self.outBand.WriteArray(outArr, 0, 0)
# flush data to disk, set the NoData value and calculate stats
		self.outBand.FlushCache()
		self.outBand.SetNoDataValue(newNoDataValue)
# georeference the image and set the projection
		self.outFi.SetGeoTransform(inFile.inData.GetGeoTransform())
		self.outFi.SetProjection(inFile.inData.GetProjection())
		del  self.outFi

#######		end of class makeGeoTiff

class chi01: #入力ファイル３つを読み込んであるという前提。
#flow directionの値の意味：真東が1で反時計回り。北が3、南東が8。
	def __init__(self, inFD, inCA, inUL, mv, nv, A0, U0):  #inFDなどはクラスInputFileのインスタンス。
		self.inDArrFD = np.array(inFD.dataArr)
		self.xsize = inFD.cols#ファイルの横幅（セル数）
		self.ysize = inFD.rows#ファイルの高さ（セル数）
		self.pixelWidth = inFD.pixelWidth
		self.pixelHeight = inFD.pixelHeight
		self.pixelDiagonal = math.sqrt(self.pixelWidth*self.pixelWidth + self.pixelHeight*self.pixelHeight)
		self.noDataValue = inFD.noDataValue#FDの元ファイルのnoData値。
		self.noDataValueCA = inCA.noDataValue#CAの元ファイルのnoData値。

		self.A0 = A0
		self.U0 = U0
		self.mv =  mv
		self. nv =  nv

		self.inDArrCA = np.array(inCA.dataArr)
		self.inDArrUL = np.array(inUL.dataArr)

		#self.outDataDfM = np.zeros((self.ysize, self.xsize), np.float64)#河口からの距離出力用配列の初期化
		self.outDataChi = np.zeros((self.ysize, self.xsize), np.float64)#Chi出力用配列の初期化
########################################チェック用のカウンタ
		self.checkCounter = 0
#########################################
########################################チェック用
#		print ("self.outDataChi [0][0]=" + str(self.outDataChi [500][900]))
########################################

		self.tmpLX=[] #一時作業のリスト。始めは空で生成。x座標用。
		self.tmpLY=[] #一時作業のリスト。始めは空で生成。y座標用。
		self.tmpLdir=[] #一時作業のリスト。始めは空で生成。方向用。
		self.nIdxX = [0, 1, 1, 0, -1, -1, -1, 0, 1] #flow directionの値とxの位置関係の対応
		self.nIdxY = [0, 0, -1, -1, -1, 0, 1, 1, 1] #flow directionの値とyの位置関係の対応
		self.nDist = [0, self.pixelWidth, self.pixelDiagonal, self.pixelHeight, self.pixelDiagonal, self.pixelWidth, self.pixelDiagonal, self.pixelHeight, self.pixelDiagonal]
		#self.nDist = [0, 1, math.sqrt(2), 1, math.sqrt(2), 1, math.sqrt(2), 1, math.sqrt(2)]

        

	def drainLine(self, tmpY_arg, tmpX_arg):
	# (mpX_arg, tmpY_arg)から落水線に沿って河口もしくは計算が終わっているセルまで移動
		FDval = self.inDArrFD[tmpY_arg][tmpX_arg]
########################################チェック用		
#		if  self.checkCounter >= 0  and  self.checkCounter <20 and FDval != self.noDataValue :
#			self.checkCounter =  self.checkCounter+1
#			print("海ではない0 @ x, y ="  + str(tmpX_arg) + ", " + str(tmpY_arg) + ", " + str(FDval))
########################################
		if FDval == self.noDataValue or self.inDArrCA[tmpY_arg][tmpX_arg]==self.noDataValueCA:	######################海だったら
			self.outDataChi[tmpY_arg][tmpX_arg]= self.noDataValue
			#self.outDataDfM[tmpY_arg][tmpX_arg] = self.noDataValue
########################################チェック用
#			if tmpY_arg > 500 and tmpY_arg < 505 and tmpX_arg>900 and tmpX_arg<905:
#				print ("海だったら @ x, y =" + str(tmpX_arg) + ", " + str(tmpY_arg) + ", " + str(int(FDval)))
########################################
			return
########################################チェック用
#		checkCounter =  checkCounter+1		
#		if  checkCounter > 0  and  checkCounter <20:
#			print("海ではない @ x, y ="  + str(tmpX_arg) + ", " + str(tmpY_arg) + ", " + str(FDval))
########################################
		self.tmpOutV = 0
		self.chi = 0
		self.tmpLX = [] #一時作業のリストを空にリセット
		self.tmpLY= []
		self.tmpLdir = []
		self.tmpSx =  tmpX_arg
		self.tmpSy =  tmpY_arg
		self.tmpLX.append(self.tmpSx)#リストに１つ目のセルを追加
		self.tmpLY.append(self.tmpSy)
		self.tmpLdir.append(int(FDval))
		while True:	#ループ；条件による脱出
			self.tmpSx +=  self.nIdxX[int(FDval)]
			self.tmpSy +=  self.nIdxY[int(FDval)]
			if self.tmpSx>= self.xsize or self.tmpSx< 0 or self.tmpSy>= self.ysize or self.tmpSy< 0:  # ファイルの範囲を出てしまう場合
				self.tmpOutV = 0
				self.chi = 0
				break
			FDval =  self.inDArrFD[self.tmpSy][self.tmpSx]
			if FDval == self.noDataValue or self.inDArrCA[self.tmpSy][self.tmpSx]==self.noDataValueCA:  ###############     海に到達
########################################チェック用
#				if self.tmpLY[ii] > 500 and self.tmpLY[ii] < 505 and self.tmpLX[ii]>900 and self.tmpLX[ii] <905:
#					print ("Fdval @ x, y =" + str(self.tmpLX[ii]) + ", " + str(self.tmpLY[ii]) + ", " + str(int(FDval)))
########################################
				self.outDataChi[self.tmpSy][self.tmpSx]= self.noDataValue
				#self.outDataDfM[self.tmpSy][self.tmpSx]= self.noDataValue
				self.tmpOutV = 0
				self.chi = 0
				break
			#elif self.outDataDfM[self.tmpSy][self.tmpSx] != 0:  #計算が終わっているセルに到達
			elif self.outDataChi[self.tmpSy][self.tmpSx] != 0:  #計算が終わっているセルに到達
				#self.tmpOutV = self.outDataDfM[self.tmpSy][self.tmpSx]
				self.chi = self.outDataChi[self.tmpSy][self.tmpSx]
########################################チェック用
#				if self.tmpLY[ii] > 500 and self.tmpLY[ii] < 505 and self.tmpLX[ii]>800 and self.tmpLX[ii] <905:
#					print ("Fdval @ x, y =" + str(self.tmpLX[ii]) + ", " + str(self.tmpLY[ii] )+ ", " + str(int(FDval)))
########################################
				break
			else:
				self.tmpLX.append(self.tmpSx)  #リストに１つ下流のセルを追加
				self.tmpLY.append(self.tmpSy)
				self.tmpLdir.append(int(FDval))
########################################チェック用
#				if self.tmpLY[ii] > 500 and self.tmpLY[ii] < 505 and self.tmpLX[ii]>800 and self.tmpLX[ii] <905:
#					print ("Fdval @ x, y =" + str(self.tmpLX[ii]) + ", " + str(self.tmpLY[ii]) + ", " + str(int(FDval)))
########################################
#
#		#############海もしくは計算が終わっているセルまで到達したので
#
#		for ii in reversed(xrange(len(self.tmpLX))): #リストを逆にたどる #python3で廃止
		for ii in reversed(range(len(self.tmpLX))): #リストを逆にたどる。
			#self.tmpOutV += self.nDist[self.tmpLdir[ii]]  #河口からの距離を計算
#			#以下chiの被積分関数
			tmp = self.inDArrUL[self.tmpLY[ii] ][ self.tmpLX[ii] ]/self.U0
########################################チェック用
			if tmp <0:
				if  self.checkCounter >= 0  and  self.checkCounter <20 and FDval != self.noDataValue :
					print("tmp before < 0, " + str(tmp))
					print( "self.inDArrUL[" + str(self.tmpLY[ii]) + "][" + str(self.tmpLX[ii]) + "] = " + str(  self.inDArrUL[self.tmpLY[ii] ][ self.tmpLX[ii] ]) )
					self.checkCounter = self.checkCounter + 1
########################################
			tmp *= math.pow(float(self.A0)/self.inDArrCA[self.tmpLY[ii] ][ self.tmpLX[ii] ], self.mv)
########################################チェック用
			if tmp <0:
				if  self.checkCounter >= 0  and  self.checkCounter <20 and FDval != self.noDataValue :
					print("tmp after < 0, " + str(tmp))
					self.checkCounter = self.checkCounter + 1
########################################			
			tmp = math.pow(tmp, 1/float(self.nv))
########################################チェック用
#			if self.tmpLY[ii] > 500 and self.tmpLY[ii] < 505 and self.tmpLX[ii]>800 and self.tmpLX[ii] <905:
#				print ("x, y =" + str(self.tmpLX[ii]) + ", " + sr(self.tmpLY[ii]) + ", " + str(tmp))
########################################
			self.chi += tmp*self.nDist[self.tmpLdir[ii]]  #Chi増分 = something * dx
			#self.outDataDfM[ self.tmpLY[ii] ][ self.tmpLX[ii] ] = self.tmpOutV#河口からの距離代入
			self.outDataChi[ self.tmpLY[ii] ][ self.tmpLX[ii] ] = self.chi  #Chi代入
########################################チェック用
#			if self.tmpLY[ii] > 500 and self.tmpLY[ii] < 505 and self.tmpLX[ii]>800 and self.tmpLX[ii] <905:
#				print ("chi @ x, y =" + str(self.tmpLX[ii]) + ", " + str(self.tmpLY[ii]) + ", " + str(self.chi))
########################################
#
#	#### end of function drainLine #####
#
#	########
	def mainCalc(self):#計算のメイン
		for ky in range(0, self.ysize):  #0からrows-1まで
			for ix in range(0, self.xsize):  #0からcols-1まで
				#if self.outDataDfM [ky][ix] == 0:   #未計算セルが見つかったら
				if self.outDataChi [ky][ix] == 0:   #未計算セルが見つかったら
########################################チェック用
#					if ky > 500 and ky < 505 and ix>900 and ix<905:
#						print (" in main 1 chi @ x, y =" + str(ix) + ", " + str(ky) + ", " + str(self.outDataChi[ky][ix]))
########################################
					self.drainLine(ky, ix)
########################################チェック用
#					if ky > 500 and ky < 505 and ix>900 and ix<905:
#						print (" in main 2 chi @ x, y =" + str(ix) + ", " + str(ky) + ", " + str(self.outDataChi[ky][ix]))
########################################
			if ky%200 == 0:
				print ("y = " + str(ky))
#
class chi01Bat:
	def __init__(self, inFpathFD, inFpathCA, inFpathUL, mv, nv, A0, U0, outFpathChi):
		#inFD = InputFile(inFpathFD)   #入力ファイル
		self.inFD = InputFile(inFpathFD)   #入力ファイル
		inCA = InputFile(inFpathCA)   #入力ファイル
		inUL = InputFile(inFpathUL)   #入力ファイル
		#chi01Inst = chi01(inFD, inCA, inUL, mv, nv, A0, U0)  #計算クラス　インスタンス化
		chi01Inst = chi01(self.inFD, inCA, inUL, mv, nv, A0, U0)  #計算クラス　インスタンス化
		chi01Inst.mainCalc()
		#outFileChi =  makeGeoTiff(inFD, chi01Inst.outDataChi, chi01Inst.noDataValue,  outFpathChi)
		#outFileChi =  makeGeoTiff(self.inFD, chi01Inst.outDataChi, chi01Inst.noDataValue,  outFpathChi)
		if outFpathChi[-4:] == ".tif":
			outFpathChi =  outFpathChi[:-4]
		outFpathChi = outFpathChi + "_" + str(mv) + "," + str(nv) + "," + str(A0) + "," + str(U0) + ".tif"
		outFileChi =  makeGeoTiff(self.inFD, chi01Inst.outDataChi, chi01Inst.noDataValue,  outFpathChi)

        
parent_name = r"C:\Users\miyar\OneDrive\デスクトップ\四年\OGIS\river"
sons_name = os.listdir(parent_name)

for river_name in sons_name:
    sons_path = parent_name + "\\" + river_name
    os.chdir(sons_path)
    print(os.getcwd(), "\n")
    all_file = os.listdir(sons_path)
#     print(all_file, "\n")
    
    
    # river_name_FlowDir.tif, river_name_D8ConA.tif, Fujiwara.tifを取得する
    FlowDir = ""
    D8ConA = ""
    Fujiwara = ""
    
    for fname in all_file:
        if fname == river_name + "_" + r"FlowDir.tif":
            FlowDir = fname 
        if fname == river_name + "_" + r"D8ConA.tif":
            D8ConA = fname
        if fname == river_name + "_" + r"Fujiwara.tif":
            Fujiwara = fname 
    print(FlowDir, D8ConA, Fujiwara)
    forderPathText = sons_path
    print(forderPathText)
    inFileNameText1 = "\\" + FlowDir	# flow directionのファイル。拡張子も必要。以下同様
    inFileNameText2 = "\\" + D8ConA	# Contributing areaのファイル
    inFileNameText3 = "\\" + Fujiwara	# 隆起速度のマップのファイル
    #outFileNameText1 = "chi_XXX.tif"	#出力ファイル名
    outFileNameText1 = "\\chi_" + river_name + ".tif" 	#出力ファイル名
    inFname1 = forderPathText + inFileNameText1	#以下4行は変更する必要なし。
    inFname2 = forderPathText + inFileNameText2
    inFname3 = forderPathText + inFileNameText3
    outFname1 = forderPathText + outFileNameText1
    
    print(inFname1, inFname2, inFname3, outFname1)

    #以下でプログラム実行。4つ目〜７つ目のパラメータは必要に応じて変えること。
    calcInst = chi01Bat(inFname1, inFname2, inFname3, 0.75, 1.95 , 1, 1, outFname1)

# 4つ目のパラメータ：stream power modelのm。
# 5つ目のパラメータ：stream power modelのn。
# 6つ目のパラメータ：stream power modelのA0。流域面積を規格化する単位流域面積。普通は1でよい。
# 7つ目のパラメータ：stream power modelのU0。隆起速度を規格化する単位隆起速度。普通は1でよい。
# A-Sプロットの近似曲線から決まるθ = m/nを参考にする。しかし、mとnは独立に決まらない。nを２（もしくは他の値）と決め打ちするか、先行研究で提案されているような方法（例えば、本流と多くの支流がχプロットで重なる値を探す）を使うか、いずれか。

        


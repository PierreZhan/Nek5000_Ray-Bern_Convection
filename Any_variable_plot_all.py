#Funktionniert. "Schöner", effizienter code.
#bei aufruf: python3 Any* "Name Nusselt"
#$2 ist optional der name des logfiles, sonst wird 'logfile' genommen

#if(nid.eq.0) write(6,*) istep,time, Nusselt, 'Nusselt'
#wichtig Nusselt groß schreiben

#################
# PLOTTET ALLE PARAMETER
#################


import numpy as np  # NumPy (multidimensional arrays, linear algebra, ...)
import re
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import os
#für aufrunden math.ceil
import math
#für plot colors:
import matplotlib.pylab as pl
#from tqdm import tqdm
import progressbar
#from progress.bar import IncrementalBar
from file_read_backwards import FileReadBackwards
import time
from datetime import date, datetime, timedelta


def conversion(sec):
	sec_value = int(sec)
	hour_value = sec_value // 3600
	sec_value %= 3600
	min_value = sec_value // 60
	sec_value %= 60
	return [hour_value, min_value, sec_value]


#Fehlermeldungen:
if len(sys.argv)<2:
	print("\nFunktionsaufruf: Programmname Variable\n")
	sys.exit()
	
if len(sys.argv)==2:
	filename = "./logfile"
if len(sys.argv)==3:
	filename = sys.argv[2]	

#anzeigen in welchem ordner das logfile sich befindet:
os.system("pwd")

#Variablen aus lofile finden:
end_step = 0
act_step = 0
end_time = 0
ekmann = "-"
visc = 0
cond = 1
runtime = 0
with open(filename, 'r') as f:
	for i, line in enumerate(f):
		######### end_step finden:
		#"..numsteps.." finden:
		if 'general:numsteps = [' in line:
			end_step = line.split('general:numsteps = [')[1].split(']\n')[0]
			end_step = int(end_step)
		# end_time finden:
		if 'general:endtime = [' in line:
			end_time = line.split('general:endtime = [')[1].split(']\n')[0]
			end_time = float(end_time)
		#Ekmann zahl rausfiltern:
		elif 'general:userparam07 = [' in line:
			ekmann = line.split('general:userparam07 = [')[1].split(']\n')[0]
			ekmann = float(ekmann)
		#viscosity rausfiltern
		elif 'velocity:viscosity = [' in line:
			visc = line.split('velocity:viscosity = [')[1].split(']\n')[0]
			visc = float(visc)
		#conductivity rausfiltern
		elif 'temperature:conductivity = [' in line:
			cond = line.split('temperature:conductivity = [')[1].split(']\n')[0]
			cond = float(cond)

		if i > 100:
			break


#anzeigen ob die simulation noch läuft:
Str_status= "(still running)"

nelx=0
nely=0
nelz=0

verteilung = ""

gestaucht="\n(gestaucht)"
equi="\n(equidistant)"
equi_nur_z="\n(gestaucht, außer in z)"


#am ende vom logfile aktuellen end_step /time raussuchen:
with FileReadBackwards(filename, encoding="utf-8") as f:
	for line in f:
		if "... EXIT ..." in line or "run successful" in line or "Terminated" in line:
			Str_status= "(terminated)"
			print("terminated")
		elif "nelx" in line:
			nelx=int(line.strip().split()[1])
		elif "nely" in line:
			nely=int(line.strip().split()[1])
		elif "nelz" in line:
			nelz=int(line.strip().split()[1])
		elif "Step " in line:
			try:
				end_step = int(line.strip().split()[1])
			except:
				end_step = int(line.strip().split()[1].split(",")[0])
			break
#wenn "... EXIT ..." nicht im logfile am ende steht, läuft es noch und wir suchen die geometrie aus dem boxfluid.box raus:
try:
	if nelx==0 and nely==0 and nelz==0:
		filename3 = "./"+os.path.dirname(filename)+"/boxfluid.box"
		lf3 = open(filename3, "r")
		for count,line in enumerate(lf3):
			if re.search('nelx', line):
				nelx = int(line.strip().split()[0])
				nely = int(line.strip().split()[1])
				try:
					nelz = int(line.strip().split()[2])
				except:
					pass
		lf3.close()
	
	if nelx<0:
		verteilung=equi
	if nelx>0:
		verteilung=gestaucht
	if nelx>0 and nelz<0:
		verteilung=equi_nur_z
except:
	pass

nelx=abs(nelx)
nely=abs(nely)
nelz=abs(nelz)

# Anzahl der elemente anzeigen:
Str_geometry = ""
if not (nelx==0 and nely==0 and nelz==0):
	if nelz==0:
		Str_geometry = "Elements\n{} x {}{}".format(nelx, nely, verteilung)
	else:
		Str_geometry = "Elements\n{} x {} x {}{}".format(nelx, nely, nelz, verteilung)

v1 = "rms_x"
v2 = "rms_y"
v3 = "rms_z"


L=1 				#FIND VARIABLE SCALE
#Prandl und Rayleight zahlen berechnen #Prandl and Rayleight calculate numbers
prandl = round(visc/cond,3)
rayleigh = round(1/(cond*visc),0)  # NO g AND NO deltaT ????
		#reynolds= round((rms_x**2+rms_y**2+rms_z**2)**0.5 *L/visc,0) 
peclet=[]
reynolds=[]

########FOR Re WAS HERE
    

#strings für den title des plots zum einfügen (formatiert)
Str_pr = "Pr={}".format(prandl)
Str_ra = "Ra={0:.1E}".format(rayleigh)
#Str_re = "Re={0:.1E}".format(reynolds)
try:
	Str_ek = "Ek={0:.1E}".format(ekmann)
except:
	Str_ek = ""






fig, ax = plt.subplots(5,1,figsize=(12,10),constrained_layout=True, sharex=True)
#fig, ax = plt.subplots(5,1,figsize=(12,10), sharex=True)

ekin=[]
nusselt=[]
nuswall=[]



rx=[]
ry=[]
rz=[]



t=[]
Steps=[]


#for line in open(filename, 'r'):
#end_step = 152273900

bar = progressbar.ProgressBar(max_value=int(end_step))
bar.colour='yellow'

#unterscheidung 3d und :
#if Ek != '-':
with open(filename, 'r') as f:
	for i, line in enumerate(f):
		if "Ekin" in line:
			t.append(float(line.strip().split()[1]))
			#Steps.append(int(line.strip().split()[0]))
			ekin.append(float(line.strip().split()[2]))
			act_step = int(line.strip().split()[0])
			#act_time = float(line.strip().split()[1])
			if i%1e6 < 20:
				#print("{:02d} %".format(int(act_time/end_time*100)))
				sys.stdout.write('\033[92m')
				sys.stdout.flush()
				bar.update(act_step)
				sys.stdout.write('\033[0m')
				sys.stdout.flush()
		elif "Nusselt" in line:
			nusselt.append(float(line.strip().split()[2]))
		elif "Nuswall" in line:
			nuswall.append(float(line.strip().split()[2]))
		elif "Peclet" in line:
			peclet.append(float(line.strip().split()[2]))
		elif "rms_x" in line:
			rx.append(float(line.strip().split()[2]))
		elif "rms_y" in line:
			ry.append(float(line.strip().split()[2]))
		elif "rms_z" in line:
			rz.append(float(line.strip().split()[2]))
		#die runtime rausfiltern:
		elif ", DT= " in line:
			hilfs = line.strip().split("Step")[1].strip() 
			runtime = float(hilfs.split()[7])

for i in range (0, len(peclet)) :
    reynolds.append(peclet[i]/prandl) ###WAS THERE UP
print("Re=",reynolds)
print("Pe=",peclet)


#damit die bar vollwird:
bar.update(end_step)
#print(end_step)
#print(act_step)


#runtime:
r = conversion(runtime)
Str_runtime = "elapsed time: {}h {}m {}s".format(r[0], r[1], r[2])

#anzeigen wie lange es noch läuft, falls es noch nicht zuende ist:
#show how long it's running if it's not over yet:

if Str_status != "(terminated)":
	rn_sec = (end_time-t[-1])/(t[-1]-t[0])*runtime
	rn = conversion(rn_sec)
	Str_status += "\n~{}h {}m left".format(rn[0], rn[1])
	#das datum wann es ca beendet:
	end_at_date = datetime.today() + timedelta(seconds=rn_sec)
	Str_status += "\n~{}h".format(end_at_date.strftime("%a %d-%m-%Y %H:%M"))



#für meine Zeit:
#for my time:
ax2 = ax[0].twiny()
ax2.set_xlabel("t (Nek5000)")
ax2.plot(t, ekin, markersize=0)


#Nusselt_mean = np.mean(Nusselt[-100:])
#Nusselt_std =  np.std(Nusselt[-100:])

#Str_Nus_mean = "    (last 10000) Mean = {}".format(round(Nusselt_mean,4))
#Str_Nus_std = "    Std = {}".format(round(Nusselt_std,4))

aniso = np.array(rz)/(np.array(rx)+np.array(ry))

			      #aniso,
var = [ekin, nuswall, nusselt,        reynolds, peclet]
col = ["g", "r", "r", "purple", "b"]
						#r"$\frac{<v_z^2>}{<v_x^2>+<v_y^2>}$"
ttl = ["Ekin", "Nu (Gradient)", "Nu (Volume)"  					, "Re", "Pe"]

t_kevin = np.array(t)/(rayleigh*prandl)**0.5

# die Mittelwerte werden berechnet ab: 200 = step 20.000
#abhier = 1000
# wenn simulation noch davor, dann mittelwerte über alles.
#if act_step < abhier*100:
#	mean_ab = 0
#else:
#	mean_ab = abhier

# die Mittelwerte werden im letzten drittel berechnet:
mean_ab = int(len(t)-len(t)/3)



for i,ar in enumerate(var):
	try:
		ax[i].plot(t_kevin, ar, color=col[i], label=ttl[i])
		ax[i].legend()
		if i == 0:
			ax[i].set_title("mean {} = {:.2e},    std={:.2e}\n\n".format(ttl[i], np.mean(ar[mean_ab:]), np.std(ar[mean_ab:])))
		else:
			ax[i].set_title("mean {} = {:.2e},    std={:.2e}".format(ttl[i], np.mean(ar[mean_ab:]),  np.std(ar[mean_ab:])))
		ax[i].plot(t_kevin[mean_ab], ar[mean_ab], marker="o", color=col[i])
		ax[i].grid(True, which='both')
		if i == 3:
			ax[i].set_yscale('log')
	except:
		#fig.delaxes(ax[i])
		print("{} kann nicht geplottet werden.".format(ttl[i]))


ax[-1].set_xlabel("t (Kevin)")


fig.suptitle(Str_pr + "   " + Str_ra + "   " + Str_ek + "\n", fontsize=16) #+ Str_re + "   "
#if Str_status != '':
#	fig.text(0.85, 0.95, Str_status, style='italic', bbox={'facecolor': 'grey', 'alpha': 0.5, 'pad': 10})

fig.text(0.88, 0.95, Str_runtime + "\n" + Str_status, horizontalalignment='center', verticalalignment='center')

fig.text(0.12, 0.95, Str_geometry, horizontalalignment='center', verticalalignment='center')


#plt.tight_layout(pad=2, w_pad=3, h_pad=3.0)
#plt.tight_layout(pad=1)
plt.show()



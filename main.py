import pydicom
import os
import shutil
import uuid
import csv

data = [['PatientName', 'uID', 'PatientID', 'PatientBirthDate', 'StudyDate', 'StudyTime', 'InstitutionName']]
dataWithNotPersonalPatientInfo = [['uID', 'countSeriesDescriptions', 'resolutionOfImages', 'Manufacturer', 'PatientAge', 'PatientSex']]


def generateCode():
    return str(uuid.uuid4())


def Anonymization(pathToFileForAnon, PatientCode):
    PatientData = []
    try:
        ds = pydicom.dcmread(pathToFileForAnon)  # считываем одиночный диком файл
    except pydicom.errors.InvalidDicomError:  # Удаляем файл, если прочитать его не удалось.
        os.remove(pathToFileForAnon)
        print("Неизвестный файл был удален")
        return
    except FileNotFoundError:
        return

    try:
        PatientData.append(ds.PatientName)
        PatientData.append(PatientCode)
        PatientData.append(ds.PatientID)
        PatientData.append(ds.PatientBirthDate)
        PatientData.append(ds.StudyDate)
        PatientData.append(ds.StudyTime)
        PatientData.append(ds.InstitutionName)

    except AttributeError:
        return

    # Модифицируем персональные данные, добавляя уникальный код.
    ds.PatientName = str(PatientCode)
    ds.PatientBirthDate = ''
    ds.PatientID = str(PatientCode)
    ds.StudyDate = ''
    ds.StudyTime = ''
    ds.InstitutionName = ''
    ds.remove_private_tags()

    pydicom.dcmwrite(pathToFileForAnon, ds)
    return PatientData


def returnDataForProgrammers(pathToFileForAnon, PatientCode, SeriesDescriptions, resolutions):

    dataForProgrammers = []
    rowAndColumns = []

    try:
        ds = pydicom.dcmread(pathToFileForAnon)  # считываем одиночный диком файл
        try:

            Rows = ds.Rows
            Columns = ds.Columns
            rowAndColumns.append(Rows)
            rowAndColumns.append(Columns)

            if ds.SeriesDescription not in SeriesDescriptions:
                if ds.SeriesDescription != '':
                    SeriesDescriptions.append(ds.SeriesDescription)
                    resolutions.append(rowAndColumns)
                else:
                    if 'UnnamedSeries' not in SeriesDescriptions:
                        SeriesDescriptions.append('UnnamedSeries')
                        resolutions.append(rowAndColumns)

        except AttributeError:
            # print("нет атрибута SeriesDescription")
            return

    except pydicom.errors.InvalidDicomError:  # Удаляем файл, если прочитать его не удалось.
        os.remove(pathToFileForAnon)
        print("Неизвестный файл был удален")
        return

    try:
        dataForProgrammers.append(PatientCode)
        dataForProgrammers.append(SeriesDescriptions)

        dataForProgrammers.append(resolutions)

        dataForProgrammers.append(ds.Manufacturer)

        age = str(ds.PatientAge)
        if age[0] != '0':
            dataForProgrammers.append(str(age[0:-1]))
        else:
            dataForProgrammers.append(str(age[1:-1]))

        if ds.PatientSex == 'F':
            dataForProgrammers.append('0')
        elif ds.PatientSex == 'M':
            dataForProgrammers.append('1')

    except AttributeError:
        return

    return dataForProgrammers


path = os.getcwd() + '\\data'  # Путь до папки с файлами
outputPath = os.getcwd() + '\\outputData'  # Путь с файлами, с удаленными перс. данными

try:
    os.mkdir(outputPath)

except OSError:
    shutil.rmtree(outputPath)  # Если папка существует, удалим ее и все ее содержимое,
    os.mkdir(outputPath)  # а затем создадим заново.
    print("Директория успешно обновлена:  %s " % outputPath)

else:
    print("Директория успешно создана:  %s " % outputPath)

PatientsDirs = os.listdir(path)
print('Всего пациентов: ' + str(len(PatientsDirs)))
counter = 0

for pathToPatientDir in PatientsDirs:

    PersonalData = []
    dataForProgrammers = []
    code = generateCode()  # генерация уникального кода для пациента
    shutil.copytree(path + '\\' + pathToPatientDir, outputPath + '\\' + code)  # Копируем файлы пациента в другую папку
    SeriesDescriptions = []
    resolutions = []  # Разрешение снимков
    for dirs, folders, files in os.walk(outputPath + '\\' + code):  # Проход по всем каталогам и файлам
        # print(dirs)
        # print(folders)
        # print(files)
        if files:
            for file in files:
                dataForProgrammers = returnDataForProgrammers(dirs + '\\' + file, code, SeriesDescriptions, resolutions)
                PersonalData = Anonymization(dirs + '\\' + file, code)

    # Проход по всем каталогам и файлам рекурсивно, для замены имён папок
    for dirs, folders, files in os.walk(outputPath + '\\' + code, topdown=False):
        if folders:
            for folder in folders:
                os.rename(dirs + '\\' + folder, dirs + '\\' + 'folder_' + generateCode())
    if PersonalData is not None:
        data.append(PersonalData)
    if dataForProgrammers is not None:
        dataWithNotPersonalPatientInfo.append(dataForProgrammers)
    counter += 1
    print('Обработано ' + str(counter) + ' из ' + str(len(PatientsDirs)))

with open('dataForDeanonimizatiom.csv', 'w', newline='') as csvfile:  # Записываем данные пользователей в csv-файл

    writer = csv.writer(csvfile)
    writer.writerows(data)

with open('dataForProgrammers.csv', 'w', newline='') as csvfile2:  # Данные пользователей для разработчиков
    writer = csv.writer(csvfile2)
    writer.writerows(dataWithNotPersonalPatientInfo)

print('Готово')

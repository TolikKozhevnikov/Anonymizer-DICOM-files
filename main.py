import pydicom
import os
import shutil
import uuid
import csv

log = []

data = [['PatientName', 'uID', 'PatientID', 'PatientBirthDate',
         'StudyDate', 'StudyTime', 'InstitutionName']]
dataWithNotPersonalPatientInfo = [['uID', 'countSeriesDescriptions', 'resolutionOfImages',
                                   'RescaleIntercept', 'RescaleSlope', 'ImagePositionPatient', 'SliceThickness',
                                   'PixelSpacing', 'TypeOfSlices', 'countOfSlices', 'Manufacturer',
                                   'DeviceSerialNumber',
                                   'PatientAge', 'PatientSex']]


# Функция, которая возвращает уникальный ключ
def generateCode():
    return str(uuid.uuid4())


# Функция, которая удаляет персональные данные из DICOM-файла, возвращает данные о пациенте, для формирования csv-файла.
def Anonymization(pathToFileForAnon, path, fileName, PatientCode, SeriesDescriptionsForAnon):
    PatientData = []
    try:
        # считываем одиночный DICOM-файл
        ds = pydicom.dcmread(pathToFileForAnon)
        # print(ds)
    # Удаляем файл, если прочитать его не удалось.
    except pydicom.errors.InvalidDicomError:
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
        # print('AttributeError')
        return

    # Модифицируем персональные данные, добавляя уникальный код.
    ds.PatientName = str(PatientCode)
    ds.PatientID = str(PatientCode)

    # Удаляем осталные персональные данные из датасета
    ds.PatientBirthDate = ''
    ds.StudyDate = ''
    ds.StudyTime = ''
    ds.InstitutionName = ''
    ds.remove_private_tags()

    # Создаем новые каталоги, для разделения файлов по полю Description,
    # формируем новый путь для DICOM-файла, в который записываем модифицированные данные из датасета,
    # Затем удаляем файл с персональными данными.
    if ds.SeriesDescription not in SeriesDescriptionsForAnon and ds.SeriesDescription != '':
        os.mkdir(path + '\\' + str(ds.SeriesDescription))
        pydicom.dcmwrite(
            path + '\\' + str(ds.SeriesDescription) + '\\' + str(fileName), ds)
        os.remove(pathToFileForAnon)
        SeriesDescriptionsForAnon.append(ds.SeriesDescription)
    elif ds.SeriesDescription not in SeriesDescriptionsForAnon and ds.SeriesDescription == '' \
            and 'UnnamedSeries' not in SeriesDescriptionsForAnon:

        os.mkdir(path + '\\' + 'UnnamedSeries')
        pydicom.dcmwrite(path + '\\' + str('UnnamedSeries') +
                         '\\' + str(fileName), ds)
        os.remove(pathToFileForAnon)
        SeriesDescriptionsForAnon.append('UnnamedSeries')
    elif ds.SeriesDescription in SeriesDescriptionsForAnon:
        try:
            pydicom.dcmwrite(
                path + '\\' + str(ds.SeriesDescription) + '\\' + str(fileName), ds)
            os.remove(pathToFileForAnon)

        except:
            os.mkdir(path + '\\' + str(ds.SeriesDescription))
            pydicom.dcmwrite(
                path + '\\' + str(ds.SeriesDescription) + '\\' + str(fileName), ds)
            os.remove(pathToFileForAnon)
            return
    elif 'UnnamedSeries' in SeriesDescriptionsForAnon:
        try:
            pydicom.dcmwrite(path + '\\' + 'UnnamedSeries' +
                             '\\' + str(fileName), ds)
            os.remove(pathToFileForAnon)

        except:
            return
    return PatientData


#   Функция возвращающая значение поля ImagePositionsPatient, если данного поля нет, возвращент None
def returnImagePositionsPatient(ds):
    try:
        return str(ds.ImagePositionPatient)

    except AttributeError:
        return 'None'


#   Функция возвращающая значение поля SliceThickness, если данного поля нет, возвращент None
def returnSliceThickness(ds):
    try:
        return str(ds.SliceThickness)
    except AttributeError:
        return 'None'


#   Функция возвращающая значение поля PixelSpacing, если данного поля нет, возвращент None
def returnPixelSpacing(ds):
    try:
        return str(ds.PixelSpacing)
    except AttributeError:
        return 'None'


#   Функция формирует список данных, необходимых для разработчиков.
def returnDataForProgrammers(pathToFileForAnon, PatientCode, SeriesDescriptions, resolutions, ImagePositionsPatient,
                             SliceThickness, PixelSpacing, counterSlices):
    dataForProgrammers = []
    rowAndColumns = []
    typeOfSlice = []
    try:
        # считываем одиночный диком файл
        ds = pydicom.dcmread(pathToFileForAnon)
        try:

            Rows = ds.Rows
            Columns = ds.Columns
            rowAndColumns.append(Rows)
            rowAndColumns.append(Columns)

            if ds.SeriesDescription not in SeriesDescriptions:
                if 'UnnamedSeries' not in SeriesDescriptions or ds.SeriesDescription != '':
                    counterSlices.append(1)
                elif 'UnnamedSeries' in SeriesDescriptions and ds.SeriesDescription == '':
                    counterSlices[-1] += 1
                if ds.SeriesDescription != '':
                    SeriesDescriptions.append(ds.SeriesDescription)
                    resolutions.append(rowAndColumns)
                    ImagePositionsPatient.append(
                        returnImagePositionsPatient(ds))
                    SliceThickness.append(returnSliceThickness(ds))
                    PixelSpacing.append(returnPixelSpacing(ds))
                else:
                    if 'UnnamedSeries' not in SeriesDescriptions:
                        SeriesDescriptions.append('UnnamedSeries')
                        resolutions.append(rowAndColumns)
                        ImagePositionsPatient.append(
                            returnImagePositionsPatient(ds))
                        SliceThickness.append(returnSliceThickness(ds))
                        PixelSpacing.append(returnPixelSpacing(ds))

            else:
                counterSlices[-1] += 1
        except AttributeError:
            # print("нет атрибута SeriesDescription")
            return

    # Удаляем файл, если прочитать его не удалось.
    except pydicom.errors.InvalidDicomError:
        os.remove(pathToFileForAnon)
        print("Неизвестный файл был удален " + str(pathToFileForAnon))
        log.append(str(pathToFileForAnon))
        return

    try:
        dataForProgrammers.append(PatientCode)
        dataForProgrammers.append(SeriesDescriptions)
        dataForProgrammers.append(resolutions)
    except AttributeError:
        return

    try:
        dataForProgrammers.append(ds.RescaleIntercept)
    except AttributeError:
        dataForProgrammers.append('None')

    try:
        dataForProgrammers.append(ds.RescaleSlope)
    except AttributeError:
        dataForProgrammers.append('None')

    try:
        dataForProgrammers.append(ImagePositionsPatient)
        dataForProgrammers.append(SliceThickness)
        dataForProgrammers.append(PixelSpacing)

        for countSlices in counterSlices:

            if countSlices < 3:
                typeOfSlice.append('Another')
            else:
                typeOfSlice.append('SeriesOfSlices')

        dataForProgrammers.append(typeOfSlice)
        dataForProgrammers.append(counterSlices)

        dataForProgrammers.append(ds.Manufacturer)
        dataForProgrammers.append(ds.DeviceSerialNumber)

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
        dataForProgrammers.append('None')

    return dataForProgrammers


path = os.getcwd() + '\\data'  # Путь до папки с файлами
# Путь с файлами, с удаленными перс. данными
outputPath = os.getcwd() + '\\outputData'

try:
    os.mkdir(outputPath)

except OSError:
    # Если папка существует, удалим ее и все ее содержимое,
    shutil.rmtree(outputPath)
    os.mkdir(outputPath)  # а затем создадим заново.
    print("Директория успешно обновлена:  %s " % outputPath)

else:
    print("Директория успешно создана:  %s " % outputPath)

PatientsDirs = os.listdir(path)
print('Всего пациентов: ' + str(len(PatientsDirs)))

#   Счетчик, для вывода процееса обработки данных о пациентах
counter = 0

#   В цикле перебераем каждого пациента из папки data
for pathToPatientDir in PatientsDirs:

    PersonalData = []
    dataForProgrammers = []
    code = generateCode()  # генерация уникального кода для пациента
    # Копируем файлы пациента в другую папку
    shutil.copytree(path + '\\' + pathToPatientDir, outputPath + '\\' + code)

    SeriesDescriptions = []
    SeriesDescriptionsForAnon = []
    resolutions = []  # Разрешение снимков

    ImagePositionsPatient = []
    SliceThickness = []
    PixelSpacing = []
    counterSlices = []

    # Проход по всем каталогам и файлам
    for dirs, folders, files in os.walk(outputPath + '\\' + code):
        # print(dirs)
        # print(folders)
        # print(files)
        if files:
            for file in files:
                dataForProgrammers = returnDataForProgrammers(dirs + '\\' + file, code, SeriesDescriptions, resolutions,
                                                              ImagePositionsPatient, SliceThickness, PixelSpacing,
                                                              counterSlices)
                PersonalData = Anonymization(
                    dirs + '\\' + file, dirs, file, code, SeriesDescriptionsForAnon)

    # Проход по всем каталогам и файлам рекурсивно, для замены имён папок на уникальные имена.
    for dirs, folders, files in os.walk(outputPath + '\\' + code, topdown=False):
        if folders:
            for folder in folders:
                if folder not in SeriesDescriptions:
                    os.rename(dirs + '\\' + folder, dirs +
                              '\\' + 'folder_' + generateCode())

    #   Добавляем в список данные о пациенте, если они присутвуют.
    if PersonalData is not None:
        data.append(PersonalData)

    #   Добавляем в список данные о пациенте, которые необходимы для разработки, если они присутвуют.
    if dataForProgrammers is not None:
        dataWithNotPersonalPatientInfo.append(dataForProgrammers)
    counter += 1
    print('Обработано ' + str(counter) + ' из ' + str(len(PatientsDirs)))

#   Запись данных в csv-файлы
# Записываем данные пользователей в csv-файл
with open('dataForDeanonimizatiom.csv', 'w', newline='') as csvfile:

    writer = csv.writer(csvfile)
    writer.writerows(data)

# Данные пользователей для разработчиков
with open('dataForProgrammers.csv', 'w', newline='') as csvfile2:
    writer = csv.writer(csvfile2)
    writer.writerows(dataWithNotPersonalPatientInfo)

with open('log.txt', 'w') as f:
    f.write(str(log))

print('Готово')

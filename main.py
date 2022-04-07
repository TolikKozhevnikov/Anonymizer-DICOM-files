import numpy as np
import nrrd
import pydicom
import os
import shutil
import uuid
import csv
import glob
import gdcm

from pathlib import Path

log = []
ErrorLog = []

data = [['PatientName', 'uID', 'PatientID', 'PatientBirthDate',
         'StudyDate', 'StudyTime', 'InstitutionName']]
dataWithNotPersonalPatientInfo = [['uID', 'countSeriesDescriptions', 'resolutionOfImages',
                                   'RescaleIntercept', 'RescaleSlope', 'ImagePositionPatient', 'SliceThickness',
                                   'PixelSpacing', 'TypeOfSlices', 'countOfSlices', 'Manufacturer',
                                   'DeviceSerialNumber',
                                   'PatientAge', 'PatientSex']]


# Функции для возврата данных из датасета

def returnPatientName(ds):
    try:
        if ds.PatientName == '':
            return 'None'
        else:
            return ds.PatientName
    except AttributeError:
        return 'None'


def returnPatientID(ds):
    try:
        if ds.PatientID == '':
            return 'None'
        else:
            return ds.PatientID
    except AttributeError:
        return 'None'
    return


def returnPatientBirthDate(ds):
    try:
        if ds.PatientBirthDate == '':
            return 'None'
        else:
            return ds.PatientBirthDate
    except AttributeError:
        return 'None'


def returnStudyDate(ds):
    try:
        if ds.StudyDate == '':
            return 'None'
        else:
            return ds.StudyDate
    except AttributeError:
        return 'None'


def returnStudyTime(ds):
    try:
        if ds.StudyTime == '':
            return 'None'
        else:
            return ds.StudyTime
    except AttributeError:
        return 'None'


def returnInstitutionName(ds):
    try:
        if ds.InstitutionName == '':
            return 'None'
        else:
            return ds.InstitutionName
    except AttributeError:
        return 'None'


# Функция, которая возвращает уникальный ключ
def generateCode():
    return str(uuid.uuid4())


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


# Функция, которая удаляет персональные данные из DICOM-файла, возвращает данные о пациенте, для формирования csv-файла.
def Anonymization(pathToFileForAnon, path, fileName, PatientCode, SeriesDescriptionsForAnon):
    PatientData = []
    try:

        # считываем одиночный DICOM-файл
        ds = pydicom.dcmread(pathToFileForAnon)

    # Удаляем файл, если прочитать его не удалось.
    except pydicom.errors.InvalidDicomError:

        os.remove(pathToFileForAnon)
        print("Неизвестный файл был удален")
        return

    except FileNotFoundError:
        print('err1')
        return

    try:
        PatientData.append(returnPatientName(ds))
        PatientData.append(PatientCode)
        PatientData.append(returnPatientID(ds))
        PatientData.append(returnPatientBirthDate(ds))
        PatientData.append(returnStudyDate(ds))
        PatientData.append(returnStudyTime(ds))
        PatientData.append(returnInstitutionName(ds))

    except AttributeError:
        print('err2')
        return

    # Модифицируем персональные данные, добавляя уникальный код.
    ds.PatientName = str(PatientCode)
    ds.PatientID = str(PatientCode)

    # Удаляем осталные персональные данные из датасета
    ds.PatientBirthDate = ''
    ds.StudyDate = ''
    ds.StudyTime = ''
    ds.InstitutionName = ''
    # ds.remove_private_tags() Убрал так как луна крашится:
    # TypeError: Could not convert value to integer without loss
    # TypeError: With tag (0018, 1405) got exception:

    # Создаем новые каталоги, для разделения файлов по полю Description,
    # формируем новый путь для DICOM-файла, в который записываем модифицированные данные из датасета,
    # Затем удаляем файл с персональными данными.
    try:
        sd = ds.SeriesDescription
        sd = str(sd).replace(" ", "")
        sd = str(sd).replace("/", "")
        sd = str(sd).replace("<", "")
        sd = str(sd).replace(">", "")

    except AttributeError:
        sd = 'UnnamedSeries'

    if sd not in SeriesDescriptionsForAnon and sd != '':
        os.mkdir(path + '/' + sd)
        pydicom.dcmwrite(
            path + '/' + sd + '/' + str(fileName), ds)
        os.remove(pathToFileForAnon)
        SeriesDescriptionsForAnon.append(sd)
    elif sd not in SeriesDescriptionsForAnon and sd == '' \
            and 'UnnamedSeries' not in SeriesDescriptionsForAnon:

        os.mkdir(path + '/' + 'UnnamedSeries')
        pydicom.dcmwrite(path + '/' + str('UnnamedSeries') +
                         '/' + str(fileName), ds)
        os.remove(pathToFileForAnon)
        SeriesDescriptionsForAnon.append('UnnamedSeries')
    elif sd in SeriesDescriptionsForAnon:

        try:
            pydicom.dcmwrite(
                path + '/' + sd + '/' + str(fileName), ds)
            os.remove(pathToFileForAnon)

        except:
            os.mkdir(path + '/' + sd)
            pydicom.dcmwrite(
                path + '/' + sd + '/' + str(fileName), ds)
            os.remove(pathToFileForAnon)

    elif 'UnnamedSeries' in SeriesDescriptionsForAnon:

        try:
            pydicom.dcmwrite(path + '/' + 'UnnamedSeries' +
                             '/' + str(fileName), ds)
            os.remove(pathToFileForAnon)

        except:
            print('err3')
            return
    # print(PatientData)
    return PatientData


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
            try:
                Rows = ds.Rows
                Columns = ds.Columns
            except AttributeError:
                Rows = 'None'
                Columns = 'None'
            rowAndColumns.append(Rows)
            rowAndColumns.append(Columns)

            # Проверяем, есть ли SeriesDescription в датасете

            try:
                SeriesDescriptionsInDs = ds.SeriesDescription

            except AttributeError:
                SeriesDescriptionsInDs = 'UnnamedSeries'

            if SeriesDescriptionsInDs not in SeriesDescriptions:
                if 'UnnamedSeries' not in SeriesDescriptions or SeriesDescriptionsInDs != '':
                    counterSlices.append(1)
                elif 'UnnamedSeries' in SeriesDescriptions and SeriesDescriptionsInDs == '':
                    counterSlices[-1] += 1
                if SeriesDescriptionsInDs != '':
                    SeriesDescriptions.append(SeriesDescriptionsInDs)
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
            print("нет атрибута SeriesDescription")
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

    except AttributeError:
        dataForProgrammers.append('None')

    try:

        age = str(ds.PatientAge)
        if age != '' or age != ' ':
            if age[0] != '0':
                dataForProgrammers.append(str(age[0:-1]))
            else:
                dataForProgrammers.append(str(age[1:-1]))
        else:
            dataForProgrammers.append('None')

    except AttributeError:

        dataForProgrammers.append('None')

    except IndexError:

        dataForProgrammers.append('None')

    try:

        if ds.PatientSex == 'F':
            dataForProgrammers.append('0')
        elif ds.PatientSex == 'M':
            dataForProgrammers.append('1')
        else:
            dataForProgrammers.append('None')

    except AttributeError:

        dataForProgrammers.append('None')

    return dataForProgrammers


def read_ct(ct_path: str) -> np.ndarray:
    """Reads CT and returns list with CT slices
    Args:
        ct_path (str): Path to directory with DICOM files
    Returns:
        np.ndarray: CT slices
    """
    ct_scan = [pydicom.dcmread(filename)
               for filename in glob.glob('{}/*.dcm'.format(ct_path))]
    ct_scan.sort(key=lambda x: int(x.InstanceNumber))
    return np.array(ct_scan)


def translate_dcm_to_nrrd(ct_scan: np.ndarray, path: str) -> None:
    """Translate given scan to nrrd file
    Args:
        ct_scan (np.ndarray): List of CT slices
        path (str): Path for saving .nrrd file
    """
    intercept = ct_scan[0].RescaleIntercept
    slope = ct_scan[0].RescaleSlope

    # make header
    header = dict()
    pos1 = ct_scan[0].ImagePositionPatient[2]
    pos2 = ct_scan[1].ImagePositionPatient[2]
    thickness = np.round(pos1 - pos2, 2)
    space_origin = np.array(ct_scan[0].ImagePositionPatient)
    space_dir_part = ct_scan[0].PixelSpacing[0]
    space_dir = np.array([[space_dir_part, 0., 0.],
                          [0., space_dir_part, 0.],
                          [0., 0., -thickness]
                          ])
    header['kinds'] = ['domain', 'domain', 'domain']
    header['space'] = 'left-posterior-superior'
    header['space directions'] = space_dir
    header['space origin'] = np.array(space_origin)
    header['intercept'] = intercept
    header['slope'] = slope

    data = translate_dcm_to_hu(ct_scan)

    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    finite_path = os.path.join(path, 'CT_Scan.nrrd')

    nrrd.write(finite_path, data, detached_header=False,
               index_order='C', header=header)


def save_as_seg_nrrd(ct_scan_path: str, mask: np.ndarray, filename: str) -> None:
    """Saves mask as .nrrd
    Args:
        ct_scan_path (str): Path to ct volume in nrrd
        mask (np.ndarray): Mask of segmentation
        filename (str): Name of segmentation (lungs, tumor, etc.)
    """
    _, header = nrrd.read(ct_scan_path, index_order='C')
    path = str(Path(ct_scan_path).parent)
    path = os.path.join(path, filename)
    nrrd.write(path, mask, detached_header=False,
               index_order='C', header=header)


def translate_dcm_to_hu(ct_scan: np.ndarray) -> np.ndarray:
    """Translates CT scan to list of normalized to HU images
    Args:
        ct_scan (np.ndarray): List of CT slices
    Returns:
        np.ndarray: Returns HU images
    """
    images = get_raw_ct_pixels(ct_scan)

    intercept = ct_scan[0].RescaleIntercept
    slope = ct_scan[0].RescaleSlope

    # convert to HU
    for n in range(len(ct_scan)):
        if slope != 1:
            images[n] = slope * images[n].astype(np.float64)
            images[n] = images[n].astype(np.int16)

        images[n] += np.int16(intercept)

    return np.array(images)


def get_raw_ct_pixels(ct_scan: np.ndarray) -> np.ndarray:
    """Returns raw pixels of each slice
    Args:
        ct_scan (np.ndarray): List of CT slices
    Returns:
        np.ndarray: List of raw pixels (images)
    """
    slices = np.stack([sl.pixel_array for sl in ct_scan])
    return np.array(slices, np.int16)


path = os.getcwd() + '/data'  # Путь до папки с файлами

# Путь с файлами, с удаленными перс. данными
outputPath = os.getcwd() + '/outputData'

f = 0

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
    # print(pathToPatientDir)
    PersonalData = []
    dataForProgrammers = []
    code = generateCode()  # генерация уникального кода для пациента

    # Копируем файлы пациента в другую папку

    try:
        shutil.copytree(path + '/' + pathToPatientDir, outputPath + '/' + code)
    except NotADirectoryError:
        print("Неизвестный файл был удален ")
        continue

    SeriesDescriptions = []
    SeriesDescriptionsForAnon = []
    resolutions = []  # Разрешение снимков
    ImagePositionsPatient = []
    SliceThickness = []
    PixelSpacing = []
    counterSlices = []

    # Проход по всем каталогам и файлам
    for dirs, folders, files in os.walk(outputPath + '/' + code):
        if files:
            for file in files:
                try:
                    pydicom.dcmread(dirs + '/' + file)
                except pydicom.errors.InvalidDicomError:
                    os.remove(dirs + '/' + file)

    for dirs, folders, files in os.walk(outputPath + '/' + code):
        # print(dirs)
        # print(folders)
        # print(files)
        if files:
            for file in files:
                dataForProgrammers = returnDataForProgrammers(dirs + '/' + file, code, SeriesDescriptions, resolutions,
                                                              ImagePositionsPatient, SliceThickness, PixelSpacing,
                                                              counterSlices)
                PersonalData = Anonymization(
                    dirs + '/' + file, dirs, file, code, SeriesDescriptionsForAnon)

    SeriesDescriptionsForFolderName = []

    for series in SeriesDescriptions:
        s = series
        s = str(s).replace(" ", "")
        s = str(s).replace("/", "")
        s = str(s).replace("<", "")
        s = str(s).replace(">", "")
        SeriesDescriptionsForFolderName.append(s)

    # Проход по всем каталогам и файлам рекурсивно, для замены имён папок на уникальные имена.

    for dirs, folders, files in os.walk(outputPath + '/' + code, topdown=False):
        if folders:
            for folder in folders:
                if folder not in SeriesDescriptionsForFolderName:
                    if not os.listdir(dirs + '/' + folder):
                        os.rmdir(dirs + '/' + folder)
                else:
                    try:
                        shutil.copytree(dirs + '/' + folder,
                                        outputPath + '/' + code + '/' + folder)
                        shutil.rmtree(dirs + '/' + folder)

                    except FileExistsError:
                        shutil.copytree(dirs + '/' + folder,
                                        outputPath + '/' + code + '/' + folder + '_' + str(generateCode())[0:4])
                        shutil.rmtree(dirs + '/' + folder)

    for dirs, folders, files in os.walk(outputPath + '/' + code):
        if folders:
            for folder in folders:

                try:
                    ct = read_ct(dirs + '/' + folder)
                    translate_dcm_to_nrrd(ct, dirs + '/' + folder)

                except AttributeError:
                    print('AttributeError ' + str(folder))

                except IndexError:
                    print('IndexError ' + str(folder))

                except ValueError:
                    print('ValueError ' + str(folder))

                else:
                    for dirsInDir, foldersInDir, filesInDir in os.walk(dirs + '/' + folder):
                        if filesInDir:
                            for file in filesInDir:
                                if str(file) != 'CT_Scan.nrrd':
                                    os.remove(dirs + '/' + folder + '/' + file)

    #   Добавляем в список данные о пациенте, если они присутвуют.

    if PersonalData:
        data.append(PersonalData)

    #   Добавляем в список данные о пациенте, которые необходимы для разработки, если они присутвуют.

    if dataForProgrammers is not None:
        dataWithNotPersonalPatientInfo.append(dataForProgrammers)
    counter += 1

    print('Обработано ' + str(counter) + ' из ' + str(len(PatientsDirs)))

#   Запись данных в csv-файлы
#   Записываем данные пользователей в csv-файл

with open('dataForDeanonimizatiom.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data)

#   Данные пользователей для разработчиков

with open('dataForProgrammers.csv', 'w', newline='') as csvfile2:
    writer = csv.writer(csvfile2)
    writer.writerows(dataWithNotPersonalPatientInfo)

with open('log.txt', 'w') as f:
    f.write(str(log))

print('Готово')

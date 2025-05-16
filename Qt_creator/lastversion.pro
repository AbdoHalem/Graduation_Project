QT += quick qml

QT += core bluetooth
CONFIG += console
CONFIG -= app_bundle



# You can make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
        bluetoothhandler.cpp \
        main.cpp \
        radialbar.cpp

RESOURCES += qml.qrc \
    qml.qrc

# Additional import path used to resolve QML modules in Qt Creator's code model
QML_IMPORT_PATH =

# Additional import path used to resolve QML modules just for Qt Quick Designer
QML_DESIGNER_IMPORT_PATH =

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

HEADERS += \
	bluetoothhandler.h \
	bluetoothmanager.h \
	radialbar.h

DISTFILES += \
    Gauge.qml \
    Screenshots/1.png \
    Screenshots/2.png \
    Screenshots/3.png \
    Screenshots/Code_Screen.png \
    Screenshots/Figma_Screen.png \
    Screenshots/file.txt \
    SideGauge.qml \
    assets/Car.svg \
    assets/Dashboard.svg \
    assets/FirstRightIcon.svg \
    assets/FirstRightIcon_grey.svg \
    assets/FourthRightIcon.svg \
    assets/FourthRightIcon_red.svg \
    assets/Light_White.svg \
    assets/Lights.svg \
    assets/Low beam headlights.svg \
    assets/Low_beam_headlights_white.svg \
    assets/Model 3.png \
    assets/Model 3.svg \
    assets/Parking lights.svg \
    assets/Parking_lights_white.svg \
    assets/Rare fog lights.svg \
    assets/Rare_fog_lights_red.svg \
    assets/SecondRightIcon.svg \
    assets/SecondRightIcon_red.svg \
    assets/Vector 1.svg \
    assets/Vector 2.svg \
    assets/Vector 70.svg \
    assets/background.png \
    assets/background.svg \
    assets/car.png \
    assets/fuel.svg \
    assets/img.txt \
    assets/needle.svg \
    assets/newcar.svg \
    assets/road.svg \
    assets/speedometer.svg \
    assets/thirdRightIcon.svg \
    assets/thirdRightIcon_red.svg \
    assets/tickmark.svg \
    img/Ellipse 1.svg \
    img/Ellipse 5.svg \
    img/Ellipse 6.svg \
    img/Rectangle 4.svg \
    img/Subtract.svg \
    img/background.png \
    img/background.svg \
    img/cirlcle.svg \
    img/img.txt \
    img/maxLimit.svg \
    img/needle.svg \
    img/ring.svg \
    img/sub.svg \
    img/tickmark.svg \
    main.qml

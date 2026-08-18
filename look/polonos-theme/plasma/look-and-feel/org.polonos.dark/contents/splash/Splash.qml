import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#161616"
    anchors.fill: parent

    property int stage: 0

    onStageChanged: {
        if (stage === 1) {
            introAnim.start();
        }
    }

    Item {
        anchors.centerIn: parent
        width: 360
        height: 380

        // Ambient Glow Backdrop
        Rectangle {
            id: glowRing
            anchors.centerIn: logoImage
            width: 200
            height: 200
            radius: 100
            color: "#c22e45"
            opacity: 0.25

            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { from: 0.15; to: 0.45; duration: 1400; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 0.45; to: 0.15; duration: 1400; easing.type: Easing.InOutQuad }
            }
        }

        // Official PolonOS Logo SVG Image
        Image {
            id: logoImage
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            width: 150
            height: 150
            source: "images/polonos-logo.svg"
            fillMode: Image.PreserveAspectFit
            smooth: true
        }

        // Title Text (Positioned well below logo to prevent any overlap)
        Text {
            id: titleText
            anchors.top: logoImage.bottom
            anchors.topMargin: 36
            anchors.horizontalCenter: parent.horizontalCenter
            text: "PolonOS"
            font.pixelSize: 34
            font.bold: true
            font.family: "Roboto"
            color: "#f4f4f5"
            opacity: 0

            NumberAnimation on opacity {
                id: introAnim
                from: 0
                to: 1
                duration: 800
                easing.type: Easing.OutCubic
            }
        }

        // Animated Loading Progress Bar
        Rectangle {
            anchors.top: titleText.bottom
            anchors.topMargin: 32
            anchors.horizontalCenter: parent.horizontalCenter
            width: 240
            height: 4
            radius: 2
            color: "#2d2d2d"

            Rectangle {
                id: progressBar
                height: parent.height
                radius: 2
                color: "#c22e45"
                width: Math.max(12, (root.stage / 6) * parent.width)

                Behavior on width {
                    NumberAnimation { duration: 350; easing.type: Easing.OutQuad }
                }
            }
        }
    }
}

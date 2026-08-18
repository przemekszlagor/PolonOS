import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#fafafa"
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
            color: "#e15265"
            opacity: 0.2

            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { from: 0.1; to: 0.35; duration: 1400; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 0.35; to: 0.1; duration: 1400; easing.type: Easing.InOutQuad }
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

        // Title Text
        Text {
            id: titleText
            anchors.top: logoImage.bottom
            anchors.topMargin: 36
            anchors.horizontalCenter: parent.horizontalCenter
            text: "PolonOS"
            font.pixelSize: 34
            font.bold: true
            font.family: "Roboto"
            color: "#27272a"
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
            color: "#e4e4e7"

            Rectangle {
                id: progressBar
                height: parent.height
                radius: 2
                color: "#e15265"
                width: Math.max(12, (root.stage / 6) * parent.width)

                Behavior on width {
                    NumberAnimation { duration: 350; easing.type: Easing.OutQuad }
                }
            }
        }
    }
}

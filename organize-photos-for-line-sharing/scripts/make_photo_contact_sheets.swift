import AppKit
import Foundation
import ImageIO

let arguments = CommandLine.arguments
guard arguments.count == 3 else {
    fputs("usage: make_photo_contact_sheets <input-dir> <output-dir>\n", stderr)
    exit(2)
}

let fileManager = FileManager.default
let inputURL = URL(fileURLWithPath: arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: arguments[2], isDirectory: true)
try fileManager.createDirectory(at: outputURL, withIntermediateDirectories: true)

let supportedExtensions = Set([
    "avif", "bmp", "dng", "gif", "heic", "heif", "jpeg", "jpg", "png", "tif", "tiff", "webp",
])
let files = try fileManager.contentsOfDirectory(
    at: inputURL,
    includingPropertiesForKeys: nil,
    options: [.skipsHiddenFiles]
).filter {
    supportedExtensions.contains($0.pathExtension.lowercased())
}.sorted {
    $0.lastPathComponent.localizedStandardCompare($1.lastPathComponent) == .orderedAscending
}

let columns = 5
let rows = 5
let pageSize = columns * rows
let cellWidth: CGFloat = 260
let cellHeight: CGFloat = 200
let imageInset: CGFloat = 8
let labelHeight: CGFloat = 22
let canvasSize = NSSize(
    width: CGFloat(columns) * cellWidth,
    height: CGFloat(rows) * cellHeight
)

let labelAttributes: [NSAttributedString.Key: Any] = [
    .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .medium),
    .foregroundColor: NSColor.black,
]

func fittedRect(for imageSize: NSSize, in bounds: NSRect) -> NSRect {
    let scale = min(bounds.width / imageSize.width, bounds.height / imageSize.height)
    let size = NSSize(width: imageSize.width * scale, height: imageSize.height * scale)
    return NSRect(
        x: bounds.midX - size.width / 2,
        y: bounds.midY - size.height / 2,
        width: size.width,
        height: size.height
    )
}

for pageStart in stride(from: 0, to: files.count, by: pageSize) {
    let pageFiles = Array(files[pageStart ..< min(pageStart + pageSize, files.count)])
    let contactSheet = NSImage(size: canvasSize)
    contactSheet.lockFocus()
    NSColor.white.setFill()
    NSRect(origin: .zero, size: canvasSize).fill()

    for (index, fileURL) in pageFiles.enumerated() {
        let column = index % columns
        let row = index / columns
        let cellX = CGFloat(column) * cellWidth
        let cellY = canvasSize.height - CGFloat(row + 1) * cellHeight
        let imageBounds = NSRect(
            x: cellX + imageInset,
            y: cellY + labelHeight + imageInset,
            width: cellWidth - imageInset * 2,
            height: cellHeight - labelHeight - imageInset * 2
        )

        if let source = CGImageSourceCreateWithURL(fileURL as CFURL, nil),
           let thumbnail = CGImageSourceCreateThumbnailAtIndex(
               source,
               0,
               [
                   kCGImageSourceCreateThumbnailFromImageAlways: true,
                   kCGImageSourceCreateThumbnailWithTransform: true,
                   kCGImageSourceThumbnailMaxPixelSize: 512,
               ] as CFDictionary
           ) {
            let image = NSImage(cgImage: thumbnail, size: .zero)
            image.draw(in: fittedRect(for: image.size, in: imageBounds))
        }

        let label = String(fileURL.deletingPathExtension().lastPathComponent.prefix(8)) as NSString
        label.draw(
            at: NSPoint(x: cellX + imageInset, y: cellY + 3),
            withAttributes: labelAttributes
        )
    }

    contactSheet.unlockFocus()
    guard let tiffData = contactSheet.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiffData),
          let jpegData = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.88]) else {
        throw NSError(domain: "ContactSheet", code: 1)
    }

    let pageNumber = pageStart / pageSize + 1
    let pageURL = outputURL.appendingPathComponent(String(format: "sheet-%02d.jpg", pageNumber))
    try jpegData.write(to: pageURL)
}

print("files=\(files.count) sheets=\((files.count + pageSize - 1) / pageSize)")

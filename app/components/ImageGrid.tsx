'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ImageResult {
  id: string;
  filename: string;
  similarity?: number;
}

interface ImageGridProps {
  images: ImageResult[];
  onDelete: (id: string) => void;
}

export default function ImageGrid({ images, onDelete }: ImageGridProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      const response = await fetch(`/api/images/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete image');
      }
      
      onDelete(id);
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('Failed to delete image');
    } finally {
      setDeletingId(null);
    }
  };

  if (images.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No images found
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {images.map((image) => (
        <div key={image.id} className="relative group">
          <div className="aspect-square relative overflow-hidden rounded-lg bg-gray-100">
            <Image
              src={`http://localhost:8000/uploads/${image.filename}`}
              alt={image.filename}
              fill
              className="object-cover"
            />
          </div>
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center opacity-0 group-hover:opacity-100">
            <button
              onClick={() => handleDelete(image.id)}
              disabled={deletingId === image.id}
              className="bg-red-500 text-white px-3 py-1 rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              {deletingId === image.id ? 'Deleting...' : 'Delete'}
            </button>
          </div>
          {image.similarity !== undefined && (
            <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
              {Math.round(image.similarity * 100)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 
'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Trash2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

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
      <div className="text-center text-muted-foreground py-8">
        No images found
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {images.map((image) => (
        <div key={image.id} className="group relative">
          <div className="aspect-square relative overflow-hidden rounded-lg bg-muted">
            <Image
              src={`http://localhost:8000/uploads/${image.filename}`}
              alt={image.filename}
              fill
              className="object-cover transition-transform group-hover:scale-105"
            />
          </div>
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/50">
            <Button 
              variant="destructive"
              size="icon"
              onClick={() => handleDelete(image.id)}
              disabled={deletingId === image.id}
            >
              {deletingId === image.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </Button>
          </div>
          {image.similarity !== undefined && (
            <div
              className="absolute top-2 right-2 px-2 py-1 rounded text-sm font-semibold bg-black/75 text-white shadow-md"
            >
              {Math.round(image.similarity)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 
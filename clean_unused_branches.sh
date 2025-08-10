#!/bin/bash
set -e

# Обновляем список веток и удаляем устаревшие remote-tracking
git fetch --prune

# Находим локальные ветки с апстримом ": gone]" и удаляем их
git branch -vv | grep ': gone]' | awk '{print $1}' | while read branch; do
    echo "Удаляю ветку: $branch"
    git branch -d "$branch" || git branch -D "$branch"
done

echo "Готово!"
